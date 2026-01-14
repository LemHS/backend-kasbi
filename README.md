# Project Setup Instructions

Follow these steps to set up the project locally:

1. **Clone the repository**

	```bash
	git clone <REPO_URL>
	```
	Replace `<REPO_URL>` with the actual repository URL.

2. **Navigate to the project directory**

	```bash
	cd backend-kasbi
	```
	Adjust the path if your project root is different.

3. **Synchronize Python dependencies with uv**

	```bash
	uv sync
	```
	This will install all required dependencies as specified in `pyproject.toml`.

4. **Make the .env file like the example .env.example**

5. **Start the fastapi webservice**

    ```bash
	cd src/app
    uv run main.py
	```

6. **To see api documentation add /docs to url**

---
