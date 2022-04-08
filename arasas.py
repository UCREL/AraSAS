import sys
import os
import argparse
import pprint
import re
import time
import json
from nltk import sent_tokenize
from camel_tools.tokenizers.word import simple_word_tokenize
from camel_tools.tokenizers.morphological import MorphologicalTokenizer
from camel_tools.disambig.mle import MLEDisambiguator
from camel_tools.morphology.database import MorphologyDB
from camel_tools.morphology.analyzer import Analyzer

only_numbers = re.compile(r"^\d+$")

# Functions to strip additional information from lemma according to https://github.com/CAMeL-Lab/camel_tools/issues/12
lemma_markers = re.compile(r'.*?((-|_).*)')
strip_lemma = lambda x: str(x).split("-")[0].split("_")[0].strip()
strip_markers = lambda x: lemma_markers.sub(r'\1', str(x)).strip()

def annotate(text, output_format="vertical", lexicon="arasas_lexicon.usas", xml_full_tags=False):
    """Annotate a given string
    It performs sentence segmentation, tokenization, disambiguation, and looks for semantic tags in the lexicon
    The output will be in the selected format, be it "vertical", "horizontal" or "xml"
    """
    string = list()
    output = list()
    types = set()
    log = {
        'tokens': 0, 
        'tokens_Z99': 0, 
        'tokens_PUNC': 0,
        'disambiguation': 0.0, 
        'sem_tagging': 0.0, 
        'tokenization': 0.0
        }

    # Loading CAMeL database
    t1 = time.time()
    if not os.path.isdir(MorphologyDB.list_builtin_dbs()[0][5]):
        sys.stderr.write("Downloading camel_data...\n")
        os.system("camel_data light")
        db = MorphologyDB.builtin_db()
        analyzer = Analyzer(db)
        disambiguator = MLEDisambiguator(analyzer)
    else:
        db = MorphologyDB.builtin_db()
        disambiguator = MLEDisambiguator.pretrained()
    log['camel_initialization'] = time.time() - t1

    # Open the lexicon and create a dictionary with each lemma and its semantic tags
    t1 = time.time()
    lex = dict()
    with open(lexicon, encoding="utf-8") as f:
        lex = {x.split("\t")[0].strip() + x.split("\t")[2].strip(): x.split("\t")[1] 
            for x in f.read().splitlines() if not x.lower().startswith("lemma")}
    log['lexicon_initialization'] = time.time() - t1

    # Sentences segmentation
    t1 = time.time()
    text = text.replace("؟", "?")
    sentences = list()
    text_split = text.split("\n")
    for line in text_split:
        if not line.strip().startswith("#"): # Avoid tagging file headers
            try:
                sentences.extend(sent_tokenize(line))
            except:
                import nltk
                nltk.download('punkt')
                sentences.extend(sent_tokenize(line))
    log['sentence_segmentation'] = time.time() - t1
    log['sentences'] = len(sentences)

    # Pipeline for each sentence
    t1 = time.time()
    
    for s, sentence in enumerate(sentences):
        # Tokenization
        t1 = time.time()
        new_sentence = []
        words = simple_word_tokenize(sentence) 
        log['tokenization'] += time.time() - t1

        # Disambiguation
        t1 = time.time()
        disamb_words = disambiguator.disambiguate(words)
        log['disambiguation'] += time.time() - t1

        # Pipeline for each disambiguated word
        t1 = time.time()
        for w, word in enumerate(disamb_words):
            
            # In case the disambiguator can't find analyses, return empty values
            word = {
                'form': word[0],
                'pos': word[1][0][1]['pos'] if word[1] else '',
                'lex': word[1][0][1]['lex'] if word[1] else '',
                'gloss': word[1][0][1]['gloss'] if word[1] else '',
            }

            # Add to number of tokens and types
            log['tokens'] += 1
            types.add(word['form'])

            # Three different ways to find semantic tags in lexicon
            # First, we check for the whole CAMeL lemma in the lexicon;
            # Second, we check for the lemma with additional info stripped away (third column from the lexicon)
            # Third, we check if the word is a number (either by POS of regex) or a punctuation (by POS)
            # Otherwise, the tag is "Z99"
            if word['lex'] in lex and lex[word['lex']] != "Z99":
                word['sema'] = lex[word['lex']]
            elif strip_lemma(word['lex']) in lex and lex[strip_lemma(word['lex'])] != "Z99":
                word['sema'] = lex[strip_lemma(word['lex'])]
            elif word['form'] in lex and lex[word['form']] != "Z99":
                word['sema'] = lex[word['form']]
            elif word['pos'] == "digit" or only_numbers.match(word['form']):
                word['sema'] = "N1 T1.2 T3 T1.3 N3.2"
            elif word['pos'] == 'punc':
                word['sema'] = "PUNC"
                log['tokens_PUNC'] += 1
            else:
                word['sema'] = "Z99"
                log['tokens_Z99'] += 1

            # Printing output (vertical is the default one)
            if not output_format or output_format == "vertical":
                string.append("{}\t{}\t{}".format(
                    word['pos'],
                    word['form'], 
                    word['sema']
                ))
            elif output_format == "horizontal":
                string.append("{}{} ".format(
                    word['form'],
                    "_" + word['sema'].split(" ")[0] if word['sema'] else ""
                ))
            elif output_format == "xml":
                string.append('<w id="{}" pos="{}" sem="{}">{}</w>'.format(
                    f"{s+1}.{w+1}",
                    word['pos'],
                    word['sema'].split(" " if not xml_full_tags else "xml-full-tags")[0],
                    word['form']
                ))

            new_sentence.append(word)

        string.append("\n")
        output.append(new_sentence)
        log['sem_tagging'] += time.time() - t1

    log['types'] = len(types)
    log['token_coverage'] = 1 - (log['tokens_Z99']/log['tokens'])
    log['token_coverage_without_punc'] = 1 - (log['tokens_Z99']/(log['tokens']-log['tokens_PUNC']))
        
    return {
        'string': "".join(string).strip() if output_format in ["horizontal"] else "\n".join(string).replace("\n\n", "\n").strip(), 
        'log': log,
        'output': output,
        }


if __name__ == "__main__": 
    """When the script is called through CLI,
    reads arguments and loads file
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="Path to file containing text in Arabic.")
    parser.add_argument("--output-file", help="Save the output to a given file.")
    parser.add_argument("--output-format", choices=["horizontal", "vertical", "xml"], help="The format in which the output will be displayed. Default: vertical.")
    parser.add_argument("--lexicon", default="arasas_lexicon.usas", help="The lexicon file from which the words will be semantically annotated. Default: arasas_lexicon.usas.")
    parser.add_argument("--log", action="store_true", help="Display a log for the tagging performance.")
    parser.add_argument("--xml-full-tags", action="store_true", help="In the XML output format, display all semantic tags instead of only the first one.")
    args = parser.parse_args()

    # Looking for exceptions
    if not os.path.isfile(args.input_file):
        sys.stderr.write("Input file {} not found.\n".format(args.input_file))
    else:
        try:
            with open(args.input_file, encoding="utf-8") as f:
                text = f.read().replace("\ufeff", "") # Remove BOM signs
        except Exception as e:
            sys.stderr.write("Error while reading input file {}.\n{}\n".format(args.input_file, str(e)))
            exit()
    if not os.path.isfile(args.lexicon):
        sys.stderr.write("Lexicon file {} not found.\n".format(args.lexicon))
        exit()
    else:
        try:
            with open(args.lexicon, encoding="utf-8") as f:
                lexicon = f.read()
        except Exception as e:
            sys.stderr.write("Error while reading lexicon {}.\n{}\n".format(args.lexicon, str(e)))
            exit()
    
    # Strip XML tags
    if args.input_file.lower().endswith(".xml"):
        text = re.sub(r"<.*?>", "", text)

    annotation = annotate(text, args.output_format, args.lexicon, xml_full_tags=args.xml_full_tags)
    
    # Write to stdout
    if not args.output_file:
        sys.stdout.write(annotation['string'] + ("\n\n" + json.dumps(annotation['log'], ensure_ascii=False, indent=4) if args.log else "") + "\n")
    else:
        sys.stdout = open(args.output_file, 'w', encoding="utf-8")
        sys.stdout.write((json.dumps(annotation['log'], ensure_ascii=False, indent=4) + "\n\n" if args.log else "") + annotation['string'])
        sys.stdout.close()
