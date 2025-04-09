# Backlog Excellence Chatbot

Backlog Excellence Chatbot is a Flask-based web application that integrates with Azure DevOps and uses OpenAI's ChatGPT API to manage and interact with work items via natural language. The application supports features such as:

- User authentication and profile management.
- Task creation, assignment updates, time tracking updates, and status updates.
- Natural language parsing via OpenAI to extract user intent.
- Listing tasks (all, pending, high-priority, completed, or assigned to the user).
- Deleting tasks and chat history.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Installation](#installation)
- [Execution Procedure](#execution-procedure)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [License](#license)

## Features

- **Task Management:** Create, update, and delete work items via a natural language interface.
- **NLP Integration:** Uses OpenAI API to extract structured commands from free-form text.
- **Azure DevOps Integration:** Retrieves and updates work items directly in Azure DevOps.
- **Chat History Management:** Persists chat history in the database with an option to delete history.
- **User Authentication:** Secure login and user profiles with Flask-Login.

## Prerequisites

- Python 3.x
- An Azure DevOps account with a Personal Access Token (PAT)
- An OpenAI API key
- Git (if cloning from a repository)

## Environment Setup

Before executing the application, you need to create a `.env` file in the project root (this file is not tracked by Git). The file must include the following environment variables:

```env
SECRET_KEY=your_flask_secret_key
AZURE_DEVOPS_ORG=your_azure_devops_organization
AZURE_DEVOPS_PROJECT=your_azure_devops_project_name
AZURE_DEVOPS_PAT=your_azure_devops_personal_access_token
OPENAI_API_KEY=your_openai_api_key
    
