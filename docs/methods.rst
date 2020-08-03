Methods
=======

In this article, we discuss the analysis and machine learning model for
predicting whether a job is predominantly software job or not. We discuss data
collection, preparing and training the model. We discuss the performance
metrics and use the model to predict software job classification for jobs from
2014--2019. The article is divided into the following sections:

.. contents:: :local:

Data collection
---------------

Data for jobs was obtained from https://jobs.ac.uk by scraping the website.
Each job has a unique id of the form AAANN. Then the data is cleaned and we
ensure that at least the following attributes are there for each job in our
dataset:

* **Job Title**: Title of the job, like Research Associate, Research Software
  Engineer, Lecturer, etc. We use text features from the job title as one of
  our features.

* **Description**: This key contains the description of the job. We use text
  features from the description as one of our features.

* **Date of publishing**: The date the job was published. This is essential to
  do an analysis over time.

* **Salary**: This information is essential for our analysis. The salary can be
  a single value or a range of values depending on experience.

* **Employer**: This is the employer that posted the job. We are only
  interested in universities in the United Kingdom. Therefore we use a list of
  all universities in UK and only keep the ones that matches an element in that
  list.

* **Type of role**: This field is an array of the type of job is given. It can
  be one or more of these values: [Academic or Research, Professional or
  Managerial, Technical, Clerical, Craft or Manual, PhD, Masters]. We use this
  to ignore PhD or Master positions for job predictions as we are not
  interested in them.

The cleaned data is stored in a database.

Training data
-------------

We use supervised classification for the data, so we need labels. To classify
the jobs in two categories we needed to have a training dataset. We asked
experts to read a subset of jobs as presented on a website (without pictures)
in which category that jobs fallen into. They had the choice between 4 options:

* This job is **mostly** for a software development position (*most*).
* This jobs requires **some** software development (*some*).
* This jobs does **not** require software development (*none*).
* There is not enough information to decide (*NA*).

Each job was shown several times (up to three times) to different experts until
a consensus emerged. A job is classified as software job if two participants
assigned *most* or *some* to the question: how much of this person's time would
be spent developing software? If no consensus emerged, a third rater was used
to derive a majority rating. Only jobs with a clear classification were kept
for building the model. We performed an inter-rater reliability calculation
using Krippendorff's alpha, and obtained alpha = 0.6774 for the first two
raters. We do not include the third rater as the third rater did not rate all
the data, but if we do, we obtain an alpha of 0.6116. Thus the data just
crosses the minimum acceptable threshold for data analysis, and it is generally
recommended to have alpha above 0.800. We can only rely on this training data
as a tentative signal for a software job. Ideally we should try to obtain
better, more consistent ratings, either by using more expert raters with
a clearly defined set of questions or many raters, such as in crowdsourcing.

Features
--------

We use text features from the description and job title to train our model. The
other job attributes are not expected to have any relationship with whether it
is a software job or not (such as employer or salary). This is particularly
true for academic software jobs as many of them have a salary in the UK on the
same scale as postdoctoral research associates.

For text features, the standard is to use TF-IDF with some mixture of n-grams.
We chose to use unigrams and bigrams as they provide sufficient information
without being noisy. We perform standard text cleaning operations such as
removing stopwords, punctuation, currency symbols.

We use information gain to get an understanding of which features are relevant.
Most of the features are not very predictive, so we keep the first 24,000 n-grams
for description, out of a total of 133,300 n-grams.  Job title has relatively fewer
text, so we keep all of the 4,308 n-grams from job title. Altogether, we then have
28,308 features.

Model
-----

We train a set of supervised classifiers on our dataset and select the model
with the best mean precision across 5 folds of the data. As our dataset is
unbalanced, accuracy is not a good measure for evaluating model performance.
Precision which is defined as the ratio of true positives to all predicted
positives is a better metric for us, because (i) we want to have a very low
proportion of false positives, and (ii) we are not as interested in ensuring
low false negatives: classifying a software job as a non-software job. With
a high precision we can then assert that the number of jobs is an underestimate
of the total number of jobs. If we get high recall (proportion of actual
software jobs predicted correctly), then we can additionally claim that the
obtained classification of software jobs is close to the actual number.

**Classifiers**. We trained the following supervised classifiers: support
vector machines, logistic regression, random forests (ensemble of decision
trees), single decision tree classifier and gradient boosting classifier. The
best model is selected and hyperparameters tuned sing nested cross validation.
In simple cross validation, the dataset is split into K folds, with K-1 folds
used for training, and the other used for model evaluation. The average score
across the folds is then compared for the different hyperparameters and the
hyperparameter with the best performance is chosen. However, this leads to the
model evaluation being conflated with the parameter selection, with the same
test set being used for both. This can risk our model appearing better than it
is (Cowley and Talbot 2010).

**Nested cross validation**. This issue is rectified by performing nested cross
validation. The inner loop selects the best model and tunes the parameters, and
the outer loop evaluates the model. We use 5 folds for both the inner and outer
loops, using stratified fold which preserves the proportion of jobs in each
class (our dataset is unbalanced, with more non-software jobs than software
jobs). For each model, we obtain a set of metrics. While we want to optimise
for precision, we also want a high enough recall. One way of accomplishing this
is by using the F1 score which is the harmonic mean of the precision and
recall. However, the F1 gives equal weight to both precision and recall. While
we could have experimented with variations of weighted F1 score, we opted for
the following model selection criterion: select the model with a precision
above 0.90 and with the highest recall. Following this selection criterion, we
obtained the chosen model as the logistic regression model with C = 10000,
balanced class weights and the L-BFGS solver. It has the following metrics:

================== ======
Metric             Value
================== ======
Precision          0.9007
Recall             0.3549
Balanced accuracy  0.6688
F1                 0.4914
ROC AUC            0.9093
=================  ======

**Model ensemble**. To obtain confidence intervals for the probability
estimates obtained from logistic regression, we create a model ensemble by
doing 100 different splits of the training data and using that to train the
best model while keeping the hyperparameters fixed.

Prediction
----------

We predict using the model ensemble for a dataset collected from 2014--2019,
containing 344,012 jobs. Of these, only 335,437 had both the description and job title correctly parsed from the jobs.ac.uk data. We further drop based on the following criteria:

* After dropping jobs without salary: 274,913
* After dropping jobs without posted: 274,912
* After dropping jobs at PhD level: 260,821

Using the ensemble we generate 100 different predictions for each job from
which we obtain bootstrap confidence intervals and estimates for the
probability for each job. The probability bound is used to generate upper and
lower bounds of the total number of jobs.

Out of the 260,821 jobs, there were 33,704 (32000--35,413, based on 95% CI of
probability being greater than 0.5) jobs classified. This translates to
a proportion of 12.9% (95% CI 12.3--13.6%) of all jobs being classified as
requiring some software development. We note that the precision is high while
recall is low. The model is conservative; the target job type is precisely
identified with few false positives, but in doing so, the model fails to
identify many jobs. The reported estimates should be considered an
underestimate for the target job type. Out of the 33,704 jobs classified as
software jobs, 513 (1.5% of all software jobs) had the words 'research' and
'software' in their job title, explicitly indicating their nature. This metric
can be used to track adoption of the nomenclature of research software
engineering in the UK academic job market. Out of the 33,704 software jobs,
25,634 (76.1%) were fixed term and 6,738 (20.0%) were permanent positions.
