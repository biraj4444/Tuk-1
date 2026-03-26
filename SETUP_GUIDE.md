# Setup Guide

This guide provides detailed instructions for setting up various services in the `tuk-1` repository. Below are the sections for MongoDB, Razorpay, Google OAuth, Cloudinary, MapTiler, and Redis configuration.

## 1. MongoDB Configuration

### Installation
1. Download and install MongoDB from the official website: [MongoDB Download Center](https://www.mongodb.com/try/download/community).
2. Follow the installation instructions for your operating system.

### Basic Setup
1. Start MongoDB server:
   ```bash
   mongod
   ```
2. Connect to the MongoDB shell:
   ```bash
   mongo
   ```
3. Create a new database:
   ```bash
   use your_database_name
   ```
4. Set up collections as needed.

## 2. Razorpay Configuration

### Setup Account
1. Sign up for a Razorpay account at [Razorpay](https://razorpay.com/).
2. Create a new application in the Razorpay dashboard to get API keys.

### API Integration
1. Install Razorpay package:
   ```bash
   npm install razorpay
   ```
2. Use the following template to integrate Razorpay API:
   ```javascript
   const Razorpay = require('razorpay');
   const instance = new Razorpay({
     key_id: 'YOUR_KEY_ID',
     key_secret: 'YOUR_KEY_SECRET'
   });
   ```

## 3. Google OAuth Configuration

### Setting Up a Project
1. Go to the [Google Developers Console](https://console.developers.google.com/) and create a new project.
2. Navigate to the `Credentials` section and create OAuth 2.0 credentials.

### Implementing Google Sign-In
1. Include the Google API script:
   ```html
   <script src="https://apis.google.com/js/platform.js" async defer></script>
   ```
2. Use the following code:
   ```javascript
   // Google Sign-In implementation here
   ```

## 4. Cloudinary Configuration

### Create an Account
1. Sign up at [Cloudinary](https://cloudinary.com/) and log into the dashboard.
2. Find your API credentials in the dashboard.

### Integration
1. Install Cloudinary package:
   ```bash
   npm install cloudinary
   ```
2. Configure Cloudinary in your application:
   ```javascript
   const cloudinary = require('cloudinary').v2;
   cloudinary.config({
     cloud_name: 'YOUR_CLOUD_NAME',
     api_key: 'YOUR_API_KEY',
     api_secret: 'YOUR_API_SECRET'
   });
   ```

## 5. MapTiler Configuration

### Register and Obtain API Key
1. Go to [MapTiler](https://www.maptiler.com/) and create an account.
2. Access your API key from your account dashboard.

### Using MapTiler
1. Include the MapTiler library in your project:
   ```html
   <script src="https://api.maptiler.com/maps/xyz.js"></script>
   ```
2. Use the API key to initialize the map.

## 6. Redis Configuration

### Install Redis
1. Follow instructions on the [Redis website](https://redis.io/download) to install Redis.

### Basic Commands
1. Start the Redis server:
   ```bash
   redis-server
   ```
2. Connect to the Redis CLI:
   ```bash
   redis-cli
   ```
3. Basic commands to use:
   ```bash
   SET key value
   GET key
   ```


## Conclusion

This guide provides a comprehensive setup for MongoDB, Razorpay, Google OAuth, Cloudinary, MapTiler, and Redis. Ensure that you replace placeholder values with your actual credentials during the configurations.