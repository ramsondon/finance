** PERSONA **
You are a professional prompt Engineer in Finance Software-Engineering and Software-Architecture.

** OBJECTIVE **
Create the following prompt to guide an AI to generate the Software described.

** ** System Description **
    You create an application which is capable of analying bank accounts of users. The application offers a login 
    via Google Authentication. It should be configurable if only given users in the settings can connect or if any Google user can login.
    After login the user can create multiple bank accounts. Each bank account can have multiple transactions.
    The user should be able to see statistics about his bank accounts and transactions. The statistics should include
    total balance, income vs. expenses, and monthly trends.
    The application should have a modern and responsive design.
    The transactions can be imported via CSV files. The application should automatically categorize transactions based on
    predefined rules which the user can configure.
    Create a Service which abstracts access to AI models to provide insights about the user's spending habits and suggest ways to save money.
    As default configurable instance you use Ollama running locally. Make sure to design the service in a way that other AI model providers can be integrated easily.
    create a settings_local.py which is gitignored to override sensitive settings like database credentials and Google OAuth credentials.
    Use Docker and Docker Compose to containerize the application and its dependencies for easy deployment.
    Ollama should also run in a separate container. Make sure the application can communicate with the Ollama container and with Ollama running on localhost.
    In Development user Ollama running on localhost. In Production use the Ollama container.
    Choose frontend and backend technologies that are widely used and have good community support.
    Ensure the application is secure, scalable, and maintainable.

** ** Requirements **
    - Docker Python 3.13 full
    - Django 6.x
    - django REST framework,
    - PostgreSQL, 
    - React served via Django templates. 
    - Use django partials of django 6 where applicable for React components.
    - latest tailwind.css for styling.
    - Redis with CELERY for and background tasks.
