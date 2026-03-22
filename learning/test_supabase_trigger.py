import unittest
from unittest.mock import patch, MagicMock
from adaptive_learning.supabase_service import SupabaseService

class TestSupabaseTrigger(unittest.TestCase):
    
    @patch('adaptive_learning.supabase_service.SupabaseService.get_session_count_today')
    @patch('adaptive_learning.supabase_service.SupabaseService.trigger_scraper')
    def test_threshold_logic(self, mock_trigger, mock_count):
        # Case 1: Count is 2 (below threshold)
        mock_count.return_value = 2
        SupabaseService.check_and_scrape("Python")
        mock_trigger.assert_not_called()
        
        # Case 2: Count is 3 (at threshold)
        mock_count.return_value = 3
        SupabaseService.check_and_scrape("Python")
        mock_trigger.assert_called_once_with("Python")
        
        mock_trigger.reset_mock()
        
        # Case 3: Count is 5 (above threshold)
        mock_count.return_value = 5
        SupabaseService.check_and_scrape("Python")
        mock_trigger.assert_called_once_with("Python")

    @patch('subprocess.Popen')
    def test_trigger_scraper(self, mock_popen):
        # Mock process
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        
        topic = "Machine Learning"
        result = SupabaseService.trigger_scraper(topic)
        
        self.assertTrue(result)
        # Check if subprocess.Popen was called with correct arguments
        args, kwargs = mock_popen.call_args
        command = args[0]
        self.assertIn("main.py", command[1])
        self.assertIn("--topic", command)
        self.assertIn(topic, command)

if __name__ == '__main__':
    unittest.main()
