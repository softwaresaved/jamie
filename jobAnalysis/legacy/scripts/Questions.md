To Do
=====

Questions from Mario
====================

* Plot occurrence of programming languages across time.

  I think the signal is too low for this to be useful.

* Determine correlations between computer language occurrences.

  Can use the R `findAssocs`. Can see if `n-grams` are useful
  for this purpose.

* Find a better way for determining *software jobs*.

* Check correlation between Subject and computer language used.

Questions from Simon
====================

* How fine-grained will our identification be?

  Can we only identify jobs that include some software development
  as part of the role? Or can we identify one set of jobs where
  software development is the major part of the role (i.e. Research
  Software Engineers) and another set where software development is
  only a minor part of the role?

  The answer to this one will dictate how the rest of the study is
  conducted.

  For the remainder of this email, I will refer to all of these jobs
  as "software roles".

---

* Can we summarise the main attributes of software roles

  Average salary, average contract type, location distribution.

  At the moment can pick out salaries, location distribution but
  we do not have a good way of determining software jobs.

---

* How many software roles are being advertised, and has the rate
  changed over the duration of the data collection?

  I do not think we have a good way of classifying software jobs
  at the moment.

---

* What job titles are given to people who do software roles?

  Looking for a frequency analysis here. Will need to do some cleaning
  of data to convert "senior postdoctoral researcher in biostimulation"
  into "Postdoctoral researcher", etc.

---

* What skills do people want from software roles?

  Again, frequency analysis. I'm also interested in grouping of skills
  if that occurs (I'd expect that it does).  

---

* Is there any way we can glean information about a hierarchy of
  software roles (i.e. evidence of career progression)?

  Possibly from names of role (i.e. "senior software developer"),
  from salary ranges or from information about managing other people?

Answered Questions
==================

* **Mario**: Work out percentages of software jobs per institution.
  * See this [article](https://github.com/softwaresaved/jobs-analysis/wiki#percentage-of-software-jobs-in-the-russell-group) 

* **Mario** Work out percentages of software jobs in the Russell group.
  * See this [article](https://github.com/softwaresaved/jobs-analysis/wiki#percentage-of-software-jobs-in-the-russell-group)

* **Mario** Establish how many jobs in IT and Computer Science are classified
  as software jobs and how many are not.

  See this [article](https://github.com/softwaresaved/jobs-analysis/wiki#consistency-of-the-classifier).

Completed Items
===============

* Separate the currency from the salary and specify it in a different column.

  Only picking up currencies that have a pound sign associated with them. Not
  going to create a new column.

* Remove commas from the salary.

  Done.

