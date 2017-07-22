"""A module that computes statistics for grades received in a set of courses."""

import argparse
import collections
import csv
import random

import matplotlib.pyplot
import numpy
import tabulate

_Course = collections.namedtuple('Course', ['code', 'grades'])


def _course_cmp(x, y):
  """A comparator function for courses.

  Redacted courses are randomly sorted towards the bottom of the list. Otherwise
  the original ordering is preserved.

  Args:
    x: The first course to be compared.
    y: The second course to be compared.

  Returns:
    -1 if x is 'Redacted,' 1 if y is 'Redacted,' 0 otherwise.
  """
  if x.code == 'Redacted' and y.code == 'Redacted':
    return random.randint(-1, 1)
  elif x.code == 'Redacted':
    return 1
  elif y.code == 'Redacted':
    return -1

  return 0


class GradeStatistics(object):
  """A class that computes statistics for grades over a set of courses."""

  def __init__(self,
               input_filename,
               skip_header=True,
               course_code_whitelist=None):
    """Initializes grades statistics data from an input file.

    The input file is expected to have two columns: one for the course code and
    another containing a comma-separated list of values. e.g.

        Course,Grades
        MATH 151,"0.95,1,1,1,1,1,1,1,0.96,0.99,1.05,0.81"
        MATH 152,"1.0667,1,1,1,1,1,1,1,1.01,0.98,0.99,1.1"

    A header is optional, but is expected by default.

    If a course code whitelist is present, those courses not present in that
    list will have their course code redacted. For example, if the course code
    "MATH 151" is contained in the whitelist, then the output will have the
    following form:

        Course Code      Minimum    First Quartile    Median    Third Quartile    Maximum
        -------------  ---------  ----------------  --------  ----------------  ---------
        MATH 151            0.81            0.9825         1            1            1.05
        Redacted            0.98            1              1            1.0025       1.1

    Args:
      input_filename: A CSV file containing the course code and a
          comma-separated list of grades.
      skip_header: Whether to skip the first line of the input file.
      course_code_whitelist: A list of course codes that may be displayed. If
          omitted, all course codes are displayed.
    """
    self._courses = []
    with open(input_filename, 'rb') as csvfile:
      reader = csv.reader(csvfile)
      if skip_header:
        reader.next()

      for row in reader:
        if course_code_whitelist is None or (course_code_whitelist and
                                             row[0] in course_code_whitelist):
          code = row[0]
        else:
          code = 'Redacted'

        data = []
        if row[1]:
          for i in row[1].split(','):
            try:
              data.append(float(i))
            except ValueError:
              continue

        self._courses.append(_Course(code, data))

      self._courses = sorted(self._courses, _course_cmp)

  def get_table(self):
    """Creates a five number summary for each course's grade distribution.

    Returns:
      A formatted table with each row containing the course code, minimum, first
      quartile, median, third quartile, and maximum grade.
    """
    table = []
    for course in self._courses:
      if not course.grades:
        table.append([course.code, None, None, None, None, None])
        continue

      table.append([
          course.code, min(course.grades), numpy.percentile(course.grades, 25),
          numpy.median(course.grades), numpy.percentile(course.grades, 75),
          max(course.grades)
      ])

    return tabulate.tabulate(
        table,
        headers=[
            'Course Code', 'Minimum', 'First Quartile', 'Median',
            'Third Quartile', 'Maximum'
        ])

  def get_box_plots(self, x_axis_label):
    """Creates box plots for each course's grade distribution.

    Args:
      x_axis_label: The x axis label.

    Returns:
      A figure containing box plots for each course's grade distribution.
    """
    fig = matplotlib.pyplot.figure()
    matplotlib.pyplot.boxplot(
        [i.grades for i in self._courses],
        labels=[i.code for i in self._courses],
        vert=False,
        whis='range',
        whiskerprops={'linestyle': '-'})
    matplotlib.pyplot.gca().invert_yaxis()
    matplotlib.pyplot.gca().set_xlim(0)
    matplotlib.pyplot.grid()
    matplotlib.pyplot.xlabel(x_axis_label)
    fig.tight_layout()
    return fig


def main():
  """Parses command line arguments and outputs grade statistics."""
  # Parse command line arguments.
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--input_filename',
      help='The CSV file containing grades to be plotted.',
      required=True)
  parser.add_argument(
      '--output_filename',
      help='The output filename where box plot images where be written.',
      required=True)
  parser.add_argument(
      '--course_code_whitelist',
      action='append',
      help=('A list of course codes that may be displayed. All course codes '
            'will be displayed if this argument is omitted.'))
  parser.add_argument(
      '--x_axis_label', default='Percent Grade', help='The x axis label.')
  args = parser.parse_args()

  # Generate grade statistics.
  stats = GradeStatistics(
      args.input_filename,
      skip_header=True,
      course_code_whitelist=args.course_code_whitelist)
  print stats.get_table()
  stats.get_box_plots(args.x_axis_label).savefig(args.output_filename)


if __name__ == '__main__':
  main()
