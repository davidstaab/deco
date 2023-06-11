# De-Co
*(like a codec in reverse)*

What if LLMs (or, more specifically, agent-chains built around them) could make our communication more efficient? Using ChatGPT to summarize long documents is already common. Maybe they can summarize the messages we leave one another, too.

De-Co is a toy I've built to answer that question. It takes spoken input from a user (as text or voice), removes speech inefficiencies, optimizes it to get down to the point, and then spits out text or voice to replace the original. I've seen it take 10 minute rambling monologues and turn them into 4 minute messages.

Ultimately, this project is a chance to keep my thumb on the pulse of explosive change around large language models. I don't intend for it to compete in the attention economy (much less the commercial economy) with various similar projects. It's just a personal hobby project to hammer on once in awhile. When I see a tool or model that looks like it'll be influential in the LLM market, I can use this project to learn how to implement it.

## Usage
### Environment setup
1. Export your OpenAI API key to your environment as `OPENAI_API_KEY`. (Use a .env file if like; the application will import it.)
1. Add Google TTS access to your Google Cloud account
1. Install the Google Cloud SDK
1. Pull the repo, then `conda env create --file environment.yml`

### To use it as a command line app with STDIN and STDOUT
The executable is called `deco.py`.
1. Run `chmod +x deco.py` on your machine.
1. Copy or move the project folder whever you store your utilities.
1. Add the application to your PATH:
    1. Edit your shell configuration file, which is typically `~/.bashrc`, `~/.bash_profile`, or `~/.zshrc` depending on your shell and operating system:
        1. Add this line to the file: `export PATH=$PATH:{Path to deco's folder}` where `{Path to deco's folder}` is wherever you put it, i.e. "~/utils". In that case, the full line would be `export PATH=$PATH:$HOME/utils`.
        1. If you want that to take effect without closing your terminal window, run `source ~/.bashrc` (or whichever file you added it to.)

## License
[GPL3](../LICENSE)

## Features

TODO
