Please note that the raw data in this directory should not be made public.

# Files

The `jobs.csv` file required to run a lot of the processing scripts
is far too big to host in this repository but can be obtained from
the SSI svn. It is a flattened version of all the job files.

* `InUK.txt` - a semi-colon delimited file with all the locations identifying whether a location is in the UK (1) or not (0)
* `SoftEngJobIDs.txt` - a list of job ids that are classed under the "Software Engineering" subject area.
* `jobs.txt` - list of job identifiers generated between 5am on the 1/6 and 5am on 4/6.
* `skippedjobs.txt` - list of the job ids that are not processed, mostly enhanced jobs.
* Training data sets
   * `marioclass.csv` - classification by Mario of a job set.
   * `gavinclass.csv` - classification by Gavin of the same job set.
   * `training1.csv`  - training data set. Jobs classified as a "Yes","Maybe","No".
   * `training2.csv`  - same training data set with "Maybe"s remapped to "Yes".
   * `training3.csv`  - "Yes" mapped to "1" and "No" mapped to "0".

# Contents of the job.csv file

The `jobs.csv` is a flattened version of the job description file. The columns 
are:

* **JobId** - a unique identifier for each job taken from the job provider.
* **Name** - the name used for the job used as the title for the job.
* **Employer** - employer identified from the html excerpt - this is pulled from an `href` tag which provides a more uniform description for each institution.
* **Location** - the Location pulled from the job. Format for this is not uniform. Also when a list of locations is provided these are not separated into the 
                 distinct locations but are treated as a single location entity in itself.
* **InUK** - determines whether a job is in the UK or not - this uses a look-up table in the `InUK.txt` file which is maintained by hand. A job in the 
             UK is specifed using a `1`, otherwise it is a `0`.
* **SoftwareJob** - determines whether a job is a software job or not. A job is classifed as a software job if it has any of the following terms 
             (case insensitive search): 
** `software developer`|`coding`|`coder`|`research software engineer`|`software engineer`|`programming`|`programmer`|`Fortran`|`C++`|`Java`|`JavaScript`|
   `Matlab`|`python|perl`
* **SoftTermIn** - indicate whether the software term is found in the title (`T`) or the body (`B`) or nowhere (`N`).
* **Salary** - the unprocess salary field
* **SalaryMin** - the minimum salary where it can be identified from the Salaray field.
* **SalaryMax** - the maximum saraly where it can be identified from the Salaray field.
* **Hours** - contracted hours as specified in the job ad.
* **Contract** - whether the jobs is full time/part time/etc as specified in the job ad. 
* **Placed on** - the date of when the job was added.
* **Closes** - the date of when the job closes.
* **Job Ref** - the job reference as provided by the job supplier.
* **h1** - a list of all the h1 titles in the file.
* **h2** - a list of all the h2 titles in the file.
* **h3** - a list of all the h3 titles in the file.
* **Type/Role** - Type of role as defined in the job ad.
* **Subject Area** - Semicolon delimited list of subject areas as specified in the job ad.
* **Location2** - a second geographica classifier as specified in the job ad.
* **Description** - the main description for the job. This is the main body of the text that gives a description of the job.

