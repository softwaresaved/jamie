# Machine learning

This document has information on the machine learning model, limitations, and
possible extensions.

## Training data

### Where do I get training data from?

Training data obtained from jobs.ac.uk is copyrighted, and thus cannot be
distributed with this repository. You can build your own training dataset by
asking expert coders ol using crowdsourcing to rate jobs on a [Likert
scale](https://en.wikipedia.org/wiki/Likert_scale). We used the question "How
much time would be spent in this job developing software?", with answers None
(1), Some (2), Most (3) and an option for insufficient evidence (NA). These
answers have to be aggregated to give a single classification of whether the
job is mostly software or not.

A previous version of this software used to collect the training data directly
from a survey application via a SQL database. This functionality is no longer
present. Instead a `snapshots/<training-snapshot>/training_set.csv` must be
present in the [correct schema](jamie/types.py#L209), where
`<training-snapshot>` is a slightly altered ISO8601 format of
YYYY-MM-DDTHH-MM-SS.

**Including training data in study**. The previous version automatically
filtered out training data which had a location outside the UK and were of PhD
or Masters level. This functionality is no longer present. This should not
cause any major issues as (i) these jobs are a minority (<20%) of advertised
jobs, and (ii) classifying a job as software job or not should not depend on
the level of the job. PhD and Masters level jobs are filtered in the prediction
phase.

### Inter-rater reliability

Inter-rater reliability refers to the internal consistency in ratings of
different coders. If ratings of coders vary widely, then this could mean they
are using different concepts of significance, which would be an issue if we are
using this data to train a model. The inter-rater reliability can be measured
using various metrics, of which a widely used one is [Krippendorff's
alpha](https://en.wikipedia.org/wiki/Krippendorff%27s_alpha). It is recommended
to have a Krippendorff's alpha above 0.80 for ratings to be considered
a reliable, consistent measure. For an alpha below 0.66, the training data
should not be used at all, and for values between 0.66 and 0.80, the results
should be considered tentative.

There's a Python package for computing alpha, named
[`krippendorff`](https://pypi.org/project/krippendorff/). It is not included in
Jamie's dependencies due to license incompatibilities. The
[`reliability()`](jamie/types.py#L365) function in TrainingSnapshot creates
a table of ratings by various coders which can be used as follows, to get alpha
for the latest training snapshot:

```python
krippendorff.alpha(
    TrainingSnapshotCollection().latest().reliability().to_numpy().T,
    level_of_measurement="ordinal"
)
```

Alternatively, packages such as
[`irr`](https://cran.r-project.org/web/packages/irr/index.html) for R can also
be used.

#### Improving inter-rater reliability

The first step is to collect more data, and preferably, from more coders. For
the training set used in the current iteration, only two coders were used, with
a third for resolving ambiguities. A better approach is to use at least three
coders (preferably five), ask each coder to rate the proportion of time spent
developing software in the job on a Likert scale, and combine their responses.
This can be performed using simple tools such as mode or mean, but it is better
to use dimensionality reduction techniques such as
[item response theory](https://en.wikipedia.org/wiki/Item_response_theory) or
[principal component analysis](https://en.wikipedia.org/wiki/Principal_component_analysis).

Once the data has been reduced to a single dimension which explains most of the
variance, we can use a suitable threshold for dichotomization of the variable.
The dichotomised binary variable can then be used as labels to train the
model.

[Crowdsourcing](https://doi.org/10.3758/s13428-011-0081-0) platforms can be
used to scale the ratings process, and also make it more reproducible.

## Limitations

Currently, the model has high precision and low recall, which means we have
many false negatives (software jobs which are classified as non-software jobs).
A first step to improve is to increase the inter-rater reliability of the
training set, and looking at other supervised machine learning algorithms.
