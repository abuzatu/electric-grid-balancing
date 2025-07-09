"""Python module to send messages to Whatsapp.

Not working yet. Docker must be given the video access.

When using Xvfb to create a virtual display in a Docker container, you typically don't need to manually set the DISPLAY environment variable, as xvfb-run handles this for you. However, if you need to set it manually for some reason, you can set it to a common default value like :99.
Here's how you can set it up:
Setting the DISPLAY Environment Variable
1. Using xvfb-run:
When you use xvfb-run, it automatically sets the DISPLAY environment variable for you. You don't need to set it manually in this case.
root
The -a option automatically chooses an available display number.
2. Manually Setting DISPLAY:
If you need to set it manually, you can do so by exporting the DISPLAY variable before running your application:
root
In this setup:
:99 is a common choice for the display number.
-screen 0 1024x768x16 sets the screen size and color depth.
Dockerfile Example
If you want to set this up in a Dockerfile, you can add the following:
root
Notes
Security: Running Jupyter as root (--allow-root) is generally not recommended for production environments. Consider using a non-root user.
Port Mapping: Ensure you map the correct ports when running your Docker container to access Jupyter from your host machine.
Testing: After setting up, test your setup to ensure that pywhatkit can send messages as expected.
And even this it can not attach files?

Correct, pywhatkit is designed to send text messages via WhatsApp Web and does not support sending actual file attachments. It automates the process of sending text messages by simulating user actions in a web browser, but it doesn't have the capability to attach files.
Alternatives for Sending Files via WhatsApp
If you need to send files via WhatsApp, consider the following alternatives:
1. WhatsApp Business API:
The official WhatsApp Business API allows for sending messages, including media files, but it requires a business account and typically involves costs.
It is more complex to set up and requires server-side integration.
2. Manual Sending:
If you are using pywhatkit to automate text messages, you can manually send files through WhatsApp Web after the text message is sent.
3. Other Automation Tools:
Tools like Selenium can be used to automate web interactions, including file uploads, but this requires more complex scripting and handling of web elements.
4. Third-Party Services:
Some third-party services offer APIs for sending WhatsApp messages with attachments, but they may come with usage fees and require compliance with WhatsApp's terms of service.
Example with Selenium (Advanced)
If you are comfortable with web automation, you can use Selenium to automate the process of sending a file through WhatsApp Web. Here's a very basic outline of how you might approach this:
)
Notes:
Selenium: This approach requires setting up Selenium WebDriver and handling web elements, which can be complex and brittle if WhatsApp Web changes its layout.
Compliance: Always ensure compliance with WhatsApp's terms of service when using automation tools.

FROM python:3.11

# Install necessary packages
RUN apt-get update && apt-get install -y \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Set the DISPLAY environment variable
ENV DISPLAY=:99

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set the working directory
WORKDIR /app

# Copy your application code
COPY . /app

# Start Xvfb and Jupyter
CMD Xvfb :99 -screen 0 1024x768x16 & jupyter notebook --ip=0.0.0.0 --allow-root


If you want to set this up in a Dockerfile, you can add the following:
CMD Xvfb :99 -screen 0 1024x768x16 & jupyter notebook --ip=0.0.0.0 --allow-root

"""

# python modules
import pywhatkit as kit
import pandas as pd
from datetime import datetime


def send_whatsapp_message_with_csv_content(to_number, csv_file_path, text_message):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_file_path)

    # Convert the DataFrame to a string
    csv_content = df.to_string(index=False)

    # Combine the text message and CSV content
    combined_message = f"{text_message}\n\n{csv_content}"

    # Get current time and add a minute to schedule the message
    now = datetime.now()
    hour = now.hour
    minute = now.minute + 1

    # Send the combined message
    kit.sendwhatmsg(to_number, combined_message, hour, minute)


# Example usage
send_whatsapp_message_with_text(
    to_number="+1234567890",  # Include country code
    file_path="src/cot_setups/cot_trade_decisions.py",
    text_message="Here is the content of the file:",
)
