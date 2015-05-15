"""Unit tests for the importer module."""

from django.test import TestCase
from unittest import skip
import debate.models as m
import os.path
import logging

from debate.importer import TournamentDataImporter, TournamentDataImporterError

class TestImporter(TestCase):

    TESTDIR = "data/test/standard"
    TESTDIR_ERRORS = "data/test/errors"

    def setUp(self):
        super(TestImporter, self).setUp()

        # create tournament
        self.t = m.Tournament(slug="import-test")
        self.t.save()
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        self.importer = TournamentDataImporter(self.t, logger=logger)

    def _open_csv_file(self, dir, filename):
        path = os.path.join(dir, filename + ".csv")
        return open(path, 'r')

    def test_rounds(self):
        f = self._open_csv_file(self.TESTDIR, "rounds")
        counts, errors = self.importer.import_rounds(f)
        self.assertEqual(counts, {m.Round: 6})
        self.assertFalse(errors)

    def test_venues(self):
        f = self._open_csv_file(self.TESTDIR, "venues")
        counts, errors = self.importer.import_venues(f)
        self.assertEqual(counts, {m.VenueGroup: 7, m.Venue: 23})
        self.assertFalse(errors)

    def test_institutions(self):
        f = self._open_csv_file(self.TESTDIR, "institutions")
        counts, errors = self.importer.import_institutions(f)
        self.assertEqual(counts, {m.Institution: 14})
        self.assertFalse(errors)

    @skip("test file does not yet exist")
    def test_teams(self):
        f = self._open_csv_file(self.TESTDIR, "teams")
        counts, errors = self.importer.import_teams(self)
        self.assertEqual(counts, {m.Team: 12})
        self.assertFalse(errors)

    def test_speakers(self):
        self.test_institutions()
        f = self._open_csv_file(self.TESTDIR, "speakers")
        counts, errors = self.importer.import_speakers(f)
        self.assertEqual(counts, {m.Team: 24, m.Speaker: 72})
        self.assertFalse(errors)

    def test_adjudicators(self):
        self.test_institutions()
        f = self._open_csv_file(self.TESTDIR, "judges")
        counts, errors = self.importer.import_adjudicators(f)
        self.assertEqual(counts, {
            m.Adjudicator: 27,
            m.AdjudicatorTestScoreHistory: 27,
            })
        self.assertFalse(errors)

    @skip("test file does not yet exist")
    def test_invalid_line(self):
        pass

    @skip("test file does not yet exist")
    def test_invalid_gender(self):
        pass

    def test_blank_entry_strict(self):
        f = self._open_csv_file(self.TESTDIR_ERRORS, "venues")
        self.assertRaises(TournamentDataImporterError, self.importer.import_venues, f)

    def test_blank_entry_not_strict(self):
        f = self._open_csv_file(self.TESTDIR_ERRORS, "venues")
        self.importer.strict = False
        counts, errors = self.importer.import_venues(f)
        self.assertEqual(counts, {m.Venue: 20, m.VenueGroup: 7})
        self.assertEqual(len(errors), 3)
        self.importer.strict = True