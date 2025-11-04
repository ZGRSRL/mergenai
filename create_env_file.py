#!/usr/bin/env python3
"""
Create .env file with SAM API configuration
"""

import os

def create_env_file():
    """Create .env file with environment variables"""
    print("Creating .env file...")
    
    env_content = """# SAM API Configuration
SAM_API_KEY=your_sam_api_key_here
SAM_PUBLIC_API_KEY=your_sam_public_api_key_here

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ZGR_AI
DB_USER=postgres
DB_PASSWORD=your_database_password_here

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Application Settings
LOG_LEVEL=INFO
DOWNLOAD_PATH=downloads
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("[SUCCESS] .env file created successfully!")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create .env file: {e}")
        return False

def load_env_file():
    """Load environment variables from .env file"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("[SUCCESS] Environment variables loaded from .env file")
        return True
    except ImportError:
        print("[WARNING] python-dotenv not installed. Installing...")
        os.system("pip install python-dotenv")
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("[SUCCESS] Environment variables loaded from .env file")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load .env file: {e}")
            return False

def test_env_variables():
    """Test if environment variables are loaded"""
    print("\nTesting environment variables...")
    
    variables = [
        'SAM_API_KEY',
        'SAM_PUBLIC_API_KEY', 
        'DB_HOST',
        'DB_PORT',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD',
        'OPENAI_API_KEY'
    ]
    
    all_loaded = True
    for var in variables:
        value = os.getenv(var)
        if value:
            print(f"  ✓ {var}: {value[:10]}...")
        else:
            print(f"  ✗ {var}: Not found")
            all_loaded = False
    
    return all_loaded

def main():
    """Main function"""
    print("Environment Configuration Setup")
    print("=" * 40)
    
    # Create .env file
    if create_env_file():
        print("\n[INFO] .env file created. Now loading variables...")
        
        # Load environment variables
        if load_env_file():
            print("\n[INFO] Environment variables loaded. Testing...")
            
            # Test variables
            if test_env_variables():
                print("\n[SUCCESS] All environment variables loaded successfully!")
                print("\nYou can now run:")
                print("  python test_sam_api_key.py")
                print("  python test_real_70LART.py")
            else:
                print("\n[ERROR] Some environment variables failed to load")
        else:
            print("\n[ERROR] Failed to load .env file")
    else:
        print("\n[ERROR] Failed to create .env file")

if __name__ == "__main__":
    main()









