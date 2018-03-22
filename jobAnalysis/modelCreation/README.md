# SVM Prediction

## Populating the Mongodb with the answers from the mysql database

The information about the human classification is stored in a mysql database, while all the rest of information is stored on MongoDB. The first action to do is to import these tags into mongodb to allow an easier processing later in the line.

For development purpose, a mysql docker and a mongodocker is used.

### Instruction to launch the mariadb docker

The following command run the docker with the password `dev` and use the folder `~/data/mariadb/` to store the information on the host instead of within the container:

```bash
docker run --name $CONTAINER_NAME -p 3306:3306 -e MYSQL_ROOT_PASSWORD=$PASSWORD -v ~/data/mariadb:/var/lib/mysql mariadb
```

Still for dev purpose, the dump from the database can be found [here](http://users.ecs.soton.ac.uk/stc/live-07-12-16-11_53.sql) and being dumped in the mariadb docker using the following commands:

1. Create an empty database with the name you want to use. To do that, need to access the mysql within the docker

To access the database itself, we need to connect to the bash command line within docker and then launch the mysql command line tool

```bash
docker exec -it $CONTAINER_NAME bash
mysql -p
# Enter password:
$PASSWORD
```

To restore from a dump into the database:
```bash
docker run --rm --link $MONGODB_CONTAINER_NAME:mongo -v $BACKUP_FOLDER:/backup mongo bash -c 'mongorestore --drop --db $DB_NAME  /backup --host $MONGO_PORT_27017_TCP_ADDR'
```

Then create an empty database with the same name as the dumb

```mysql
create DATABASE $DATABASE_NAME;
```
And finally, dumping it into the mysql database

```bash
docker exec -i $CONTAINER_NAME mysql $DATABASE_NAME -uroot -pdev < ~/data/job_analysis/backup_bob/live-07-12-16-11_53.sql
```

To access to the mariadb from outside docker if the -p option is not set up, the docker ip is needed.
The command line is:

```docker
docker inspect --format '{{ .NetworkSettings.IPAddress }}' $CONTAINER_NAME
```


### Instruction to launch the mongoDB docker

The mongoDB that contains the data should have been set up during the `job2db` and `textTransformation` steps. However, to launch the mongodb docker, use the following command:

```bash
docker run -p 27017:27017 -v ~/data/mongodb/:/data/db --name mongod -d mongo`
```
And to access to the mongodb within the docker container

```bash
sudo docker exec -it mongod mongo
```
### Launching the script

The script is the [dbPreparation.py]() and just need to be run: `python3.5 dbPreparation.py`
It is launched every day with the cronjob and should not be launched manually

The script only connect to the mysql db and parse the results that are finally classified. For each of this result (one record per classification), it check if a record exists and append the lists. If the record doesn't exist, it create a new one.
When the parsing is done, it creates a new tag `done` set up as `Yes` for all records.
This is needed because the way the records are store in mysql is one record per tag, while the way it is stored in mongodb is one record per job (with a list of tags). The number of tags needed to fully classify the job can differ. It can be 2 or 3. The rules are the following:

- If we have at least two of a given answer, return that.
- If we receive three reviews, each with a separate answer, return 'Ambiguous'.
- Otherwise, return nothing and await more reviews to make a decision.

### Requirements

* Python 3.5
* `pip install -r requirements.txt`


### Source and references
* Visualise which words are the most correlated to each categories
  * https://towardsdatascience.com/multi-class-text-classification-with-scikit-learn-12f1e60e0a9f
  * https://buhrmann.github.io/tfidf-analysis.html
