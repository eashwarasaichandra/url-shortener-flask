import unittest
from app import create_app, db
from app.models import URL, Analytics
from datetime import datetime, timezone, timedelta
import json

class URLShortenerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_shorten_url(self):
        response = self.client.post('/shorten', 
                                    data=json.dumps({"url": "https://www.google.com"}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('short_code', data)
        self.assertEqual(data['original_url'], "https://www.google.com")

    def test_idempotency(self):
        # Shorten once
        response1 = self.client.post('/shorten', 
                                     data=json.dumps({"url": "https://www.google.com"}),
                                     content_type='application/json')
        code1 = json.loads(response1.data)['short_code']
        
        # Shorten again
        response2 = self.client.post('/shorten', 
                                     data=json.dumps({"url": "https://www.google.com"}),
                                     content_type='application/json')
        code2 = json.loads(response2.data)['short_code']
        
        self.assertEqual(response2.status_code, 200) # Should be 200 for reuse
        self.assertEqual(code1, code2)

    def test_redirection(self):
        self.client.post('/shorten', 
                         data=json.dumps({"url": "https://www.google.com"}),
                         content_type='application/json')
        with self.app.app_context():
            url_obj = URL.query.first()
            response = self.client.get(f'/{url_obj.short_code}')
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, "https://www.google.com")

    def test_analytics_atomic_increment(self):
        self.client.post('/shorten', 
                         data=json.dumps({"url": "https://www.google.com"}),
                         content_type='application/json')
        with self.app.app_context():
            url_obj = URL.query.first()
            
            # Click 3 times
            for _ in range(3):
                self.client.get(f'/{url_obj.short_code}')
                
            response = self.client.get(f'/analytics/{url_obj.short_code}')
            data = json.loads(response.data)
            self.assertEqual(data['click_count'], 3)

    def test_expiration(self):
        # Create an expired URL manually
        with self.app.app_context():
            expired_url = URL(
                original_url="https://expired.com",
                short_code="exp123",
                expires_at=datetime.now(timezone.utc) - timedelta(days=1)
            )
            db.session.add(expired_url)
            db.session.commit()
            
            response = self.client.get('/exp123')
            self.assertEqual(response.status_code, 410) # Gone

    def test_invalid_url(self):
        response = self.client.post('/shorten', 
                                    data=json.dumps({"url": "not-a-url"}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
