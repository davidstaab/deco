# De-Co
*(like a codec in reverse)*

## Description

What if LLMs (or, more specifically, agent-chains built around them) could make our communication more efficient? Using ChatGPT to summarize long documents is already common. Maybe they can summarize the messages we leave one another, too.

De-Co is a toy I've built to answer that question. It takes spoken input from a user (as text or voice), removes speech inefficiencies, optimizes it to get down to the point, and then spits out text or voice to replace the original. I've seen it take 10 minute rambling monologues and turn them into 4 minute messages.

Ultimately, this project is a chance to keep my thumb on the pulse of explosive change around large language models. I don't intend for it to compete in the attention economy (much less the commercial economy) with various similar projects. It's just a personal hobby project to hammer on once in awhile. When I see a tool or model that looks like it'll be influential in the LLM market, I can use this project to learn how to implement it.

## License
![See here](LICENSE)

## Installation

Pull the repo, then run `python3 -m deco`

## Usage

Provide instructions and examples for use. Include screenshots as needed.

To add a screenshot, create an `assets/images` folder in your repository and upload your screenshot to it. Then, using the relative filepath, add it to your README using the following syntax:

    ```md
    ![alt text](assets/images/screenshot.png)
    ```

## Credits

List your collaborators, if any, with links to their GitHub profiles.

If you used any third-party assets that require attribution, list the creators with links to their primary web presence in this section.

If you followed tutorials, include links to those here as well.

## License

The last section of a high-quality README file is the license. This lets other developers know what they can and cannot do with your project. If you need help choosing a license, refer to [https://choosealicense.com/](https://choosealicense.com/).

---

🏆 The previous sections are the bare minimum, and your project will ultimately determine the content of this document. You might also want to consider adding the following sections.

## Badges

![badmath](https://img.shields.io/github/languages/top/lernantino/badmath)

Badges aren't necessary, per se, but they demonstrate street cred. Badges let other developers know that you know what you're doing. Check out the badges hosted by [shields.io](https://shields.io/). You may not understand what they all represent now, but you will in time.

## Features

If your project has a lot of features, list them here.

## How to Contribute

If you created an application or package and would like other developers to contribute it, you can include guidelines for how to do so. The [Contributor Covenant](https://www.contributor-covenant.org/) is an industry standard, but you can always write your own if you'd prefer.

## Tests

Go the extra mile and write tests for your application. Then provide examples on how to run them here.

## Environment setup
1. Export your OpenAI API key to your environment as `OPENAI_API_KEY`. (Use a .env file if like; the application will import it.)
1. Add Google TTS access to your Google Cloud account
1. Install the Google Cloud SDK
1. Pull the repo, then `conda env create --file environment.yml`

## To use it as a command line app with STDIN and STDOUT
The executable is called `deco.py`.
1. Run `chmod +x deco.py` on your machine.
1. Copy or move the project folder whever you store your utilities.
1. Add the application to your PATH:
    1. Edit your shell configuration file, which is typically `~/.bashrc`, `~/.bash_profile`, or `~/.zshrc` depending on your shell and operating system:
        1. Add this line to the file: `export PATH=$PATH:{Path to deco's folder}` where `{Path to deco's folder}` is wherever you put it, i.e. "~/utils". In that case, the full line would be `export PATH=$PATH:$HOME/utils`.
        1. If you want that to take effect without closing your terminal window, run `source ~/.bashrc` (or whichever file you added it to.)

