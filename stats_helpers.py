# stats_helpers.py
# The statistics for my task.
# Every function follows a formula from the unit notes - the comments say
# which week each one comes from, and I used the "Key Python functions"
# the practicals listed for that week.

import math
import statistics
import numpy as np
from scipy import stats


def _clean(sample):
    """turn the data into a plain array of numbers and drop any NaN"""
    s = np.asarray(sample, dtype=float)
    return s[~np.isnan(s)]


def describe(sample):
    """
    DESCRIPTIVE STATISTICS - Week 2.

    The notes say data is described in two aspects, so I do both:
      - central tendency: mean, median
      - dispersion (spread): range, interquartile range, variance,
        standard deviation
    """
    s = _clean(sample)
    n = len(s)

    # --- central tendency ---
    mean = statistics.mean(s)
    median = statistics.median(s)
    # I did not calculate the mode. The notes say the mode is normally used
    # for nominal or ordinal data, and conversion rate is continuous ratio
    # data - nearly every value appears only once, so a mode would be
    # meaningless here.

    # --- dispersion ---
    smallest = float(np.min(s))
    largest = float(np.max(s))
    data_range = largest - smallest          # range = max - min

    q1 = float(np.percentile(s, 25))         # 25th percentile
    q3 = float(np.percentile(s, 75))         # 75th percentile
    iqr = q3 - q1                            # interquartile range

    # ddof=1 divides by (n - 1). That is the SAMPLE variance formula from
    # the notes, not the population one. We have a sample, so ddof=1.
    variance = float(np.var(s, ddof=1))
    std = float(np.std(s, ddof=1))           # std = square root of variance

    return {
        "n": int(n),
        "mean": round(float(mean), 4),
        "median": round(float(median), 4),
        "min": round(smallest, 4),
        "max": round(largest, 4),
        "range": round(data_range, 4),
        "q1": round(q1, 4),
        "q3": round(q3, 4),
        "iqr": round(iqr, 4),
        "variance": round(variance, 5),
        "std": round(std, 4),
    }


def check_normality(sample):
    """
    CONDITION FOR INFERENCE - Week 4, Step 3.
    The notes say to check whether the sample looks normally distributed,
    because if it doesn't "the power of p-value may be limited".

    A normal distribution is symmetric, so its mean and median are about
    the same. Skewness measures that: 0 is perfectly symmetric, and the
    common rule of thumb is that between -0.5 and +0.5 is near enough.
    """
    s = _clean(sample)
    skewness = float(stats.skew(s))
    return {
        "mean": round(float(statistics.mean(s)), 4),
        "median": round(float(statistics.median(s)), 4),
        "skewness": round(skewness, 3),
        "roughly_normal": bool(abs(skewness) < 0.5),
    }


def confidence_interval(sample, conf=0.95):
    """
    CONFIDENCE INTERVAL for the population mean - Week 3.

        CI = x-bar  ±  z* · (s / sqrt(n))

        s / sqrt(n)        is the STANDARD ERROR
        z* · s / sqrt(n)   is the MARGIN OF ERROR

    Which critical value to use? The notes give this rule:
      - sample size < 30   -> use t*  (t-distribution, df = n - 1)
      - sample size >= 30  -> use z*  (standard normal), by convention
    Our sample is 30, so this picks z* = 1.960 for 95% confidence.
    """
    s = _clean(sample)
    n = len(s)
    mean = statistics.mean(s)
    sd = np.std(s, ddof=1)

    standard_error = sd / math.sqrt(n)

    if n >= 30:
        critical = float(stats.norm.ppf((1 + conf) / 2))   # z*
        stat_used = "z*"
        df = None
    else:
        critical = float(stats.t.ppf((1 + conf) / 2, n - 1))  # t*
        stat_used = "t*"
        df = n - 1

    margin_of_error = critical * standard_error

    return {
        "conf_level": conf,
        "n": int(n),
        "mean": round(float(mean), 4),
        "standard_error": round(float(standard_error), 5),
        "statistic_used": stat_used,
        "critical_value": round(critical, 4),
        "df": df,
        "margin_of_error": round(float(margin_of_error), 5),
        "lower": round(float(mean - margin_of_error), 4),
        "upper": round(float(mean + margin_of_error), 4),
    }


def two_sample_ttest(group_a, group_b, alpha=0.05):
    """
    TWO-SAMPLE (INDEPENDENT) t-TEST - Week 4.

    The formula in the notes is:

        t* = (x-bar_1 - x-bar_2) / sqrt( s1²/n1 + s2²/n2 )

    scipy.stats.ttest_ind() does this for us. equal_var=False (Welch's
    test) is the version that keeps the two groups' variances separate,
    which is exactly the formula above. Our two groups are different sizes
    so this is the safer choice.

    Degrees of freedom: the notes take the conservative approach for a
    manual table lookup, i.e. the smaller group's n - 1.

    Decision rule from the notes: reject the null hypothesis when
    p-value <= 0.05.
    """
    a = _clean(group_a)
    b = _clean(group_b)

    t_stat, p_value = stats.ttest_ind(a, b, equal_var=False)

    reject_null = bool(p_value <= alpha)

    # A very small p-value would round away to 0.0, and "p = 0" is wrong -
    # the probability is tiny, never actually zero. So keep 4 significant
    # figures (which stays honest for numbers like 3.02e-08) and report it
    # as "< 0.0001", the way results are normally written up.
    p = float(p_value)
    p_text = "< 0.0001" if p < 0.0001 else str(round(p, 4))

    return {
        "n_a": int(len(a)),
        "n_b": int(len(b)),
        "mean_a": round(float(statistics.mean(a)), 4),
        "mean_b": round(float(statistics.mean(b)), 4),
        "std_a": round(float(np.std(a, ddof=1)), 4),
        "std_b": round(float(np.std(b, ddof=1)), 4),
        "t_stat": round(float(t_stat), 4),
        "p_value": float("%.4g" % p),
        "p_value_text": p_text,
        # smaller group's n - 1, the conservative df the notes use
        "df_conservative": int(min(len(a), len(b)) - 1),
        "alpha": alpha,
        "reject_null": reject_null,
        "significant": reject_null,
    }
