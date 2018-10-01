# Deployment

Deploying the project requires at minima the installation of a [mongodb database](https://www.mongodb.com/).
To fully deploy the project and being able to build the predictions model, a MySQL database is also needed with a dump of the trainig-set-collector and the jobs ads files contained in that training set. These information will be then pushed into the mongodb and the MYSQL database would not be longer needed.


### Config file

For any deployment, a config file needs to be filled with the location of the jobs. A template is present [here
](https://github.com/softwaresaved/jobs-analysis/blob/master/jobAnalysis/config/config_template.ini). It is adviced to copy it and change the name to avoid conflict with the repository and uploading sensitive information.

### Python requirements

**Python 3.6 and dependencies**:
It is suggested to run a virtual environment and installing all the required dependencies in it (requires Python3.6):

```bash
    pip install virtualenv --user && virtualenv venv && source venv/bin/activate
```
Then installing the all dependencies using the requirements.txt file:
```bash
pip install -r requirements.txt
```

**NLTK library**: This [python library](www.nltk.org) used to transform and clean texts needs to install [extra data](http://www.nltk.org/data.html) to be able to work. The following bash line should install all the required data. It needs to be installed only once:
```bash
python3 -c "import nltk; [nltk.download(i) for i in ['punkt', 'maxent_treebank', 'pos_tagger', 'stopwords', 'wordnet', 'averaged_perceptron', 'tagger']]"
```

### Databases
The project relies on a mongodb database to store the different jobs and to be able to store the analysis and predictions.
The following installation steps require docker but it is possible to install the database with package manager or directly from mongodb repository. In any case no further configuration is needed as the different scripts in the project take care of the data creation.


The information about the human classification is stored in a mysql database, while all the rest of information is stored on MongoDB. The first action to do is to import these tags into mongodb to allow an easier processing later in the line.


#### Instruction to launch the mongoDB docker

To launch the mongodb docker, use the following command:

```bash
sudo docker pull mongo:latest
```

```bash
docker run -p 27017:27017 -v ~/data/mongodb/:/data/db --name mongod -d mongo`
```
And to access to the mongodb within the docker container

```bash
sudo docker exec -it mongod mongo
```
#### Instruction to launch the mariadb docker
This database is used to interact with the [training-set-collector](https://github.com/softwaresaved/training-set-collector) and therefore not needed for the everyday operation. A script copies all the information from there to the mongodb.
* Installing the mariadb docker

```bash
docker pull mariadb:latest
```

```bash
docker run --name $CONTAINER_NAME -p 3306:3306 -e MYSQL_ROOT_PASSWORD=$PASSWORD -v ~/data/mariadb:/var/lib/mysql mariadb
```

1. Create an empty database with the name you want to use. To do that, need to access the mysql within the docker

To access the database itself, we need to connect to the bash command line within docker and then launch the mysql command line tool

```bash
docker exec -it $CONTAINER_NAME bash
mysql -p
# Enter password:
$PASSWORD
```

2. Then create an empty database with the same name as the dump

```mysql
create DATABASE $DATABASE_NAME;
```
3. And finally, dumping it into the mysql database

```bash
docker exec -i $CONTAINER_NAME mysql $DATABASE_NAME -uroot -p$ROOT_PASSWORD < $DUMPFILE.sql
```

To access to the mariadb from outside docker if the -p option is not set up, the docker ip is needed.
The command line is:

```docker
docker inspect --format '{{ .NetworkSettings.IPAddress }}' $CONTAINER_NAME
```
## Automating the process

The script [day_task.sh](https://github.com/softwaresaved/jobs-analysis/blob/master/day_task.sh_) launches all the day-to-day operations and automatically pushed the last version of jupyter notebooks and output to the branch [report](https://github.com/softwaresaved/jobs-analysis/tree/reports).
