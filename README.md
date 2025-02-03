# ytmusic-bot
5 hours of work to create a free, working Youtube Music bot. That is all it plays is music from youtube.

# -  Installation  -
Recommended IDE is VS Code!
 
# 1. Install dependencies!
    To install dependencies, open a terminal in python and type:
    pip install discord
    pip install yt_dlp
    pip install python-dotenv
    pip install PyNaCl

    (If 'pip install' isn't working, try 'py -m pip install package_name' instead!)

    Some dependencies like FFMPEG require a seperate method to install.
    https://youtu.be/JR36oH35Fgg - This video can explain intalling FFMPEG better than I ever could.

# 2. Create Your Bot!
    Go to https://discord.com/developers/applications and select "New Application".
    Name it whatever you like, agree to Discord's Developer TOS and click "Create"
    Select your new application, and then on the left select "Bot" and click "Reset Token"
    Scroll down and enable "Message Content Intent", Copy down your Token and paste it in "TOKEN" inside of your .py file.

# 3. Finalizing The Bot!
    Next go to "OAuth2" on the developers page, and select "bot" on the URL Generator.
    For simplicity, just select "Administrator", but this bot only really needs these few permissions;
    Connect, Speak, Use Voice Activity, Send Messages, and View Channels.

    Finally, copy the Generated URL and open it. In Discord select the server you want to add your new bot to!
    To finish up, right click the channel you want to set as the "Now Playing" Channel and copy it's ID.
    Do the same with the Discord server your bot is in, and paste both of those into their settings inside of the .py file.

    To start the bot, run your .py file, enter a Voice Channel and type /play followed by a Youtube Link!
