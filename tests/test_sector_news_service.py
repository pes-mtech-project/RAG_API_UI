import unittest

from api.app.services import sector_news_service


class BlendResultsTest(unittest.TestCase):
    def test_blend_results_orders_and_limits(self):
        doc_hits = {
            "doc1": {
                "semantic_score": 0.8,
                "bm25_score": 5.0,
                "source": {"_source": {"title": "Doc 1"}, "_index": "idx"},
                "phrase_matches": {"p1"},
                "tags_matched": {"tag1"},
            },
            "doc2": {
                "semantic_score": 0.4,
                "bm25_score": 10.0,
                "source": {"_source": {"title": "Doc 2"}, "_index": "idx"},
                "phrase_matches": {"p2"},
                "tags_matched": set(),
            },
        }

        results = sector_news_service._blend_results(doc_hits, 0.8, 10.0, limit=1, min_score=None)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "doc1")
        self.assertGreater(results[0].score, 0)

    def test_blend_results_respects_min_score(self):
        doc_hits = {
            "doc1": {
                "semantic_score": 0.1,
                "bm25_score": 1.0,
                "source": {"_source": {"title": "Doc 1"}, "_index": "idx"},
                "phrase_matches": set(),
                "tags_matched": set(),
            }
        }

        results = sector_news_service._blend_results(doc_hits, 0.1, 1.0, limit=5, min_score=1.1)
        self.assertEqual(len(results), 0)

    def test_within_date_range_handles_compact_dates(self):
        entry = {"date": "20251031000000"}
        date_from = sector_news_service._parse_datetime("2025-11-01")
        date_to = sector_news_service._parse_datetime("2025-11-15")

        self.assertFalse(sector_news_service._within_date_range(entry, date_from, date_to))


if __name__ == "__main__":
    unittest.main()
