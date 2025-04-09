# Backlog Excellence Chatbot

Backlog Excellence Chatbot is a Flask-based web application that integrates with Azure DevOps and leverages OpenAI's ChatGPT API to manage and interact with work items using natural language. This solution automates many aspects of project management—from creating and updating tasks to handling assignments and time tracking—while providing an intuitive chatbot interface for team members.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Installation](#installation)
- [Execution Procedure](#execution-procedure)
- [Usage](#usage)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Overview

Backlog Excellence Chatbot addresses the challenges teams face with manual backlog and task management. By using natural language processing and API integration, the application streamlines the process of creating, updating, and tracking work items in Azure DevOps. Whether you’re looking to reassign tasks, update time tracking, or simply list pending or completed work items, the chatbot simplifies your workflow through a friendly conversational interface.

## Features

- **Task Management:**  
  Create, update, and delete work items using natural language commands.
- **NLP Integration:**  
  Leverages OpenAI's ChatGPT API to parse user input and extract structured commands.
- **Azure DevOps Integration:**  
  Interfaces directly with Azure DevOps to retrieve and update work items.
- **Chat History Management:**  
  Persists user-chat history in a database with an option to clear it.
- **User Authentication:**  
  Provides secure login and profile management using Flask-Login.
- **Additional Commands:**  
  Supports listing tasks (all, pending, high-priority, completed, or assigned to the user) and deleting tasks.

## Prerequisites

Before running the application, ensure you have the following:
- Python 3.x
- An Azure DevOps account with a valid Personal Access Token (PAT)
- An OpenAI API key
- Git (if you plan to clone the repository)

## Environment Setup

This project uses a `.env` file to store sensitive configuration data such as API keys and tokens. **Make sure to add the `.env` file to your `.gitignore`** so it is not tracked in version control.

### Example `.env` File

```dotenv
# Flask Configuration
SECRET_KEY=your_flask_secret_key
FLASK_ENV=development

# Azure DevOps Configuration
AZURE_DEVOPS_ORG=your_azure_devops_organization_url
AZURE_DEVOPS_PROJECT=your_azure_devops_project_name
AZURE_DEVOPS_PAT=your_azure_devops_personal_access_token

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
Installation
Clone the Repository:

bash
Copy
git clone https://github.com/yourusername/backlog-excellence-chatbot.git
cd backlog-excellence-chatbot
Create and Activate a Virtual Environment:

bash
Copy
python -m venv venv
source venv/bin/activate    # For macOS/Linux
.\venv\Scripts\activate     # For Windows
Install the Dependencies:

bash
Copy
pip install -r requirements.txt
Execution Procedure
Prepare Your Environment:
Ensure your .env file (as described above) is present in the project root.

Run the Application:

bash
Copy
python app.py
Access the Application:
Open your browser and navigate to http://127.0.0.1:5000/.

Usage
User Authentication:
Register a new account and then log in.

Chatbot Features:

Task Creation:
Use commands like:
create task: Fix login bug; Critical bug in login flow; due: 2025-01-20

Task Updates:
Update task time using:
update time: task Fix login bug spent 2 remaining 3

Task Assignment:
Reassign tasks using:
update assignment: task 123 to John Doe <john@example.com>

Task Deletion:
Delete tasks by saying:
delete task: 123

Listing Tasks:
Commands such as:
list all tasks or show my tasks will retrieve tasks.

Chat History:
Use the "Delete Chat History" button in the interface to clear your past conversation.

Configuration
Azure DevOps:
Configure your organization URL, project name, and PAT in the .env file or directly in azure_devops.py if needed.

OpenAI:
Set your API key in the .env file. The file is automatically loaded by the application using python-dotenv.

Project Structure
graphql
Copy
backlog-excellence-chatbot/
├── app.py               # Main Flask application
├── azure_devops.py      # Azure DevOps API integration functions
├── openai_utils.py      # OpenAI API integration and NLP utility functions
├── .env                 # Environment variables file (not tracked by Git)
├── requirements.txt     # List of Python dependencies
├── templates/
│   ├── base.html        # Base HTML layout
│   ├── index.html       # Main chat interface
│   ├── login.html       # Login page
│   ├── register.html    # Registration page
│   └── profile.html     # User profile page
└── static/
    ├── styles.css       # CSS styles
    └── logo.png         # Project logo
Contributing
If you’d like to contribute to this project, please fork the repository and submit a pull request. For major changes, please open an issue first to discuss what you would like to change.

License
This project is licensed under the MIT License.

yaml
Copy

---

### Final Note

This README provides detailed, clear instructions for setting up, configuring, and using your Backlog Excellence Chatbot project. It includes prerequisites, installation steps, usage guidelines, and an explanation of the project structure—all of which are important for potential employers and contributors. Modify or expand on any section as required to better reflect your project specifics.

Let me know if you need further adjustments or additional sections!
