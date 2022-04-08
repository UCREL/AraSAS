# Development repo for AraSAS

This is a repository for the Arabic Semantic Analysis System (AraSAS) in Python.

There is a web demonstration app at [https://arasas.herokuapp.com](https://arasas.herokuapp.com).

- [Installing requirements](#Installing-requirements)
- [Windows encoding issue](#Windows-encoding-issue)
- [Usage](#Usage)
- [Lexicon expansion](#Lexicon-expansion)
- [Web API](#Web-API)
- [Performance](#Performance)

## Installing requirements

`$ pip3 install -r requirements.txt`

## Windows encoding issue

In case you are using Python in a Windows environment, you must set the default encoding to UTF-8 by adding the parameter `-X utf8` when calling Python (version 3.7+ is required).

`python -X utf8 arasas.py`

Other than that, one can always install [Windows Subsystem for Linux](https://docs.microsoft.com/pt-br/windows/wsl/install-win10) to avoid any compatibility issues.

## Usage

`$ python3 arasas.py -h`

```
usage: arasas.py [-h] [--output-file OUTPUT_FILE]
                 [--output-format {horizontal,vertical,xml}]
                 [--lexicon LEXICON] [--log] [--xml-full-tags]
                 input_file

positional arguments:
  input_file            Path to file containing text in Arabic.

optional arguments:
  -h, --help            show this help message and exit
  --output-file OUTPUT_FILE
                        Save the output to a given file.
  --output-format {horizontal,vertical,xml}
                        The format in which the output will be displayed.
                        Default: vertical.
  --lexicon LEXICON     The lexicon file from which the words will be
                        semantically annotated. Default: arasas_lexicon.usas.
  --log                 Display a log for the tagging performance.
  --xml-full-tags       In the XML output format, display all semantic tags
                        instead of only the first one.
```

## Web API

The web app available at [https://arasas.herokuapp.com](https://arasas.herokuapp.com) was built using the Flask framework.

### Heroku

[Procfile](Procfile) and [nltk.txt](nltk.txt) are intended for the Heroku deployment process. `camel_tools` should be installed from pypi.

### Apache2

To deploy it using Apache2, it needs WSGI for Python 3 and the file [flask/wsgi.py](flask/wsgi.py) must be modified in accordance to the environment. By default, WSGI.py points to a virtual environment inside `flask/` named "uvenv".

See this installation example for using AraSAS Web API in a Apache2/Ubuntu machine:

1) Install Apache2:

```
$ sudo apt-get update
$ sudo apt-get install apache2
```

2) Clone AraSAS repository in `/var/www`:

```
$ cd /var/www
$ sudo git clone https://github.com/UCREL/AraSAS
$ cd AraSAS
```

3) Install the needed packages and give Apache the folder ownership:

```
$ sudo chown www-data .
$ cd flask
$ sudo virtualenv -p python3 uvenv
$ sudo uvenv/bin/pip3 install -r ../requirements.txt
$ sudo uvenv/bin/pip3install -r requirements.txt
$ sudo ln ../arasas.py .
```

3) Edit `WSGI.py` file according to the folder in which AraSAS was just installed (keep untouched if you just followed this tutorial): 

$ sudo nano wsgi.py

4) Configure AraSAS virtual host inside Apache2, creating a new file and pasting the text that follows inside it (Shortcut: Ctrl+X to save the file). Remember to edit the line `ServerName` to the host domain.

```
$ sudo nano /etc/apache2/sites-available/arasas.conf
```

```
<VirtualHost *:80>
    ServerName arasas.com
    DocumentRoot /var/www/AraSAS

    WSGIDaemonProcess arasas threads=5 python-home=/var/www/AraSAS/flask/uvenv
    WSGIScriptAlias / /var/www/AraSAS/flask/wsgi.py

    <Directory /var/www/AraSAS/flask>
        WSGIProcessGroup arasas
        WSGIApplicationGroup %{GLOBAL}
        WSGIScriptReloading On
        Order deny,allow
        Allow from all
    </Directory>
</VirtualHost>
```

5) Activate the newly created virtual host:

```
$ sudo a2ensite arasas
```

6) Install and activate the `wsgi` mod:

```
$ sudo apt-get update
$ sudo apt-get install libapache2-mod-wsgi-py3
$ sudo a2enmod wsgi
```

7) Start (or restart) Apache2:

```
$ sudo service apache2 start
```

### API

Once on-line, the route `/api` receives GET requests with the following variables:

  ```
  text: the string that is going to be annotated
  style: the output format (vertical|horizontal|xml)
  ```

Example:

  ```
  https://arasas.herokuapp.com/api?text=اكتب (أو الصق) النص الخاص بك ليتم تمييزه لغويًا في هذا المربع
  ```

The output is a JSON file with the following keys:

  ```
  output: string with the output in the selected style (vertical as default)
  log: nested dictionary with relevant information concerning the tagging process
  ```

## Performance

AraSAS tagging speed may vary from 1,067 to 3,245 words tagged each second using an Intel(R) Core(TM) i5-2400 CPU @ 3.10GHz. It depends on the lexical variety of the given corpus due to the disambiguation caching (see [https://github.com/CAMeL-Lab/camel_tools/issues/21](https://github.com/CAMeL-Lab/camel_tools/issues/21)).

By using the parameter `--log` one can see the system performance in different corpora (time is measured in seconds):

1) News (coverage: 96.8% of the words were semantically tagged)
```json
{
    "tokens": 1108058,
    "tokens_Z99": 35202,
    "tokens_PUNC": 68704,
    "disambiguation": 326.01197242736816,
    "sem_tagging": 6.469516754150391,
    "tokenization": 0.523158073425293,
    "camel_initialization": 6.992664337158203,
    "lexicon_initialization": 0.08255529403686523,
    "sentence_segmentation": 1.8666191101074219,
    "sentences": 33743,
    "types": 116355,
    "token_coverage": 0.9682309048804304,
    "token_coverage_without_punc": 0.9661308851459657
}
```

2) Blogs (coverage: 96% of the words were semantically tagged)
```json
{
    "tokens": 1114535,
    "tokens_Z99": 44096,
    "tokens_PUNC": 79494,
    "disambiguation": 1026.4404141902924,
    "sem_tagging": 7.091530799865723,
    "tokenization": 0.632889986038208,
    "camel_initialization": 8.197651147842407,
    "lexicon_initialization": 0.08252573013305664,
    "sentence_segmentation": 2.7246599197387695,
    "sentences": 57992,
    "types": 156465,
    "token_coverage": 0.9604355179514327,
    "token_coverage_without_punc": 0.957396856742873
}
```
