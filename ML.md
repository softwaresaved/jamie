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

## Limitations

Currently, the model has high precision and low recall, which means we have
many false negatives (software jobs which are classified as non-software jobs).
A first step to improve is to increase the inter-rater reliability of the
training set, and looking at other supervised machine learning algorithms.
