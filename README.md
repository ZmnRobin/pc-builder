# 🖥️ PC Builder AI - Bangladesh Market

An intelligent PC build recommendation system specifically designed for the Bangladesh market. This system scrapes real-time component prices from local retailers and provides personalized PC build recommendations based on budget and usage requirements.

## ✨ Features

- **Real-time Price Scraping**: Automatically scrapes component prices from Bangladeshi retailers
- **AI-Powered Recommendations**: Smart build recommendations based on budget and purpose
- **Compatibility Checking**: Ensures all components are compatible with each other
- **Multiple Build Types**: Support for gaming, office, productivity, and content creation builds
- **Market Insights**: Price trends and availability analysis
- **RESTful API**: Complete API for integration with other applications

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- MongoDB (running locally or remotely)
- Internet connection for scraping

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd pc-builder
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start MongoDB**
   - Windows: `net start MongoDB`
   - Linux/Mac: `sudo systemctl start mongod`
   - Or run: `mongod`

4. **Run the startup script**
   ```bash
   python start.py
   ```

The API will be available at `http://localhost:8000`

## 📖 API Documentation

Once the server is running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

### Key Endpoints

- `POST /recommend-build` - Get PC build recommendation
- `GET /components` - List available components
- `POST /compare-builds` - Compare builds at different budgets
- `GET /build-templates` - Get pre-made build templates
- `GET /market-insights` - Get market analysis
- `POST /scrape-now` - Manually trigger price scraping

### Example Usage

```python
import requests

# Get a gaming PC recommendation
response = requests.post("http://localhost:8000/recommend-build", json={
    "budget": 80000,
    "purpose": "gaming_mid",
    "prefer_brands": ["AMD", "NVIDIA"]
})

build = response.json()
print(f"Total Price: ৳{build['total_price']:,}")
```

## 🏗️ Project Structure

```
pc-builder/
├── app.py              # Main FastAPI application
├── config.py           # Configuration settings
├── models.py           # Pydantic models and schemas
├── engine.py           # Recommendation engine
├── scraper.py          # Web scraping module
├── database.py         # Database utilities
├── start.py            # Startup script
├── test_api.py         # API testing script
├── requirements.txt    # Python dependencies
├── static/            # Frontend files (optional)
└── README.md          # This file
```

## 🔧 Configuration

Edit `config.py` to customize:

- **MongoDB connection**: Change `MONGODB_URL`
- **Scraping intervals**: Modify `SCRAPING_INTERVAL_HOURS`
- **Retailers**: Add/remove retailers in `RETAILERS`
- **Budget ranges**: Adjust `BUDGET_RANGES`

## 🧪 Testing

Run the test suite to verify everything is working:

```bash
python test_api.py
```

This will test all API endpoints and validate the recommendation engine.

## 📊 Build Types Supported

- **Gaming Budget** (৳25k-50k): Entry-level gaming
- **Gaming Mid-Range** (৳50k-100k): 1080p high settings
- **Gaming High-End** (৳100k+): 1440p/4K gaming
- **Office** (৳25k-40k): Productivity and office work
- **Productivity** (৳40k-80k): Enhanced productivity
- **Content Creation** (৳80k+): Video editing, streaming, 3D work

## 🔄 Automated Scraping

The system automatically scrapes component prices every 8 hours (configurable). You can also trigger manual scraping:

```bash
curl -X POST http://localhost:8000/scrape-now
```

## 🛠️ Development

### Adding New Retailers

1. Add retailer configuration to `config.py`
2. Implement scraping logic in `scraper.py`
3. Test with the scraping endpoint

### Extending Build Types

1. Add new purpose to `BuildPurpose` enum in `models.py`
2. Define budget allocation in `engine.py`
3. Implement build logic in the engine
4. Update API endpoints

## 📈 Performance

- **Scraping**: ~2-5 minutes for all components
- **Recommendations**: <1 second response time
- **Database**: Optimized with proper indexes
- **Memory**: ~100-200MB typical usage

## 🐛 Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Ensure MongoDB is running
   - Check connection string in `config.py`

2. **Scraping Errors**
   - Check internet connection
   - Verify retailer websites are accessible
   - Review logs in `scraper.log`

3. **No Components Found**
   - Run manual scraping: `POST /scrape-now`
   - Check database: `GET /health`

### Logs

- Application logs: Console output
- Scraping logs: `scraper.log`
- Database logs: MongoDB logs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- StarTech.com.bd for providing component data
- FastAPI community for the excellent framework
- MongoDB for the database solution

---

**Made with ❤️ for the Bangladesh PC building community** 
