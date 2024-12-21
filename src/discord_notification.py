from discordwebhook import Discord

import secret

WEB_HOOK_URL = secret.web_hook_url


def post_notice(web_hook_url=WEB_HOOK_URL, message='DONE!'):
    discord = Discord(url=web_hook_url)
    discord.post(content=message)
