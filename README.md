# Bugtracker-Tool

This code is presented AS-IS with no warranty or support implied or otherwise 
and provided entirely free.
 
Requires PS 7.x or >
Elements borrowed from here:  https://github.com/mjmenger/terraform-bigip-postbuild-config/blob/main/atcscript.tmpl

Requires DO and AS3 RPMs.  These can be found here:
* AS3 Releases:  https://github.com/f5networks/f5-appsvcs-extension/releases
* DO Releases:   https://github.com/F5Networks/f5-declarative-onboarding/releases

Ensure that the references to in the playbook to RPMs match the filenames/versions you download.  It is also advisable that you update the $schema reference at the top of the script.

# Wolverine

## About

Give your python scripts regenerative healing abilities!

Run your scripts with Wolverine and when they crash, GPT-4 edits them and explains what went wrong. Even if you have many bugs it will repeatedly rerun until it's fixed.

For a quick demonstration see my [demo video on twitter](https://twitter.com/bio_bootloader/status/1636880208304431104).

## Setup

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

Add your openAI api key to `openai_key.txt` - _warning!_ by default this uses GPT-4 and may make many repeated calls to the api.

## Example Usage

To run with gpt-4 (the default, tested option):

    python wolverine.py buggy_script.py "subtract" 20 3

You can also run with other models, but be warned they may not adhere to the edit format as well:

    python wolverine.py --model=gpt-3.5-turbo buggy_script.py "subtract" 20 3

## Future Plans

This is just a quick prototype I threw together in a few hours. There are many possible extensions and contributions are welcome:

- add flags to customize usage, such as asking for user confirmation before running changed code
- further iterations on the edit format that GPT responds in. Currently it struggles a bit with indentation, but I'm sure that can be improved
- a suite of example buggy files that we can test prompts on to ensure reliablity and measure improvement
- multiple files / codebases: send GPT everything that appears in the stacktrace
- graceful handling of large files - should we just send GPT relevant classes / functions?
- extension to languages other than python

# Size Limit [![Cult Of Martians][cult-img]][cult]

<img src="https://ai.github.io/size-limit/logo.svg" align="right"
     alt="Size Limit logo by Anton Lovchikov" width="120" height="178">

Size Limit is a performance budget tool for JavaScript. It checks every commit
on CI, calculates the real cost of your JS for end-users and throws an error
if the cost exceeds the limit.

* **ES modules** and **tree-shaking** support.
* Add Size Limit to **GitHub Actions**, **Circle CI** or another CI system
  to know if a pull request adds a massive dependency.
* **Modular** to fit different use cases: big JS applications
  that use their own bundler or small npm libraries with many files.
* Can calculate **the time** it would take a browser
  to download and **execute** your JS. Time is a much more accurate
  and understandable metric compared to the size in bytes.
* Calculations include **all dependencies and polyfills**
  used in your JS.

<p align="center">
  <img src="./img/example.png" alt="Size Limit CLI" width="738">
</p>

With **[GitHub action]** Size Limit will post bundle size changes as a comment
in pull request discussion.

<p align="center">
<img src="https://raw.githubusercontent.com/andresz1/size-limit-action/master/assets/pr.png"
  alt="Size Limit comment in pull request about bundle size changes"
  width="686" height="289">
</p>

With `--why`, Size Limit can tell you *why* your library is of this size
and show the real cost of all your internal dependencies.
We are using [Statoscope] for this analysis.

<p align="center">
  <img src="./img/why.png" alt="Statoscope example" width="650">
</p>

<p align="center">
  <a href="https://evilmartians.com/?utm_source=size-limit">
    <img src="https://evilmartians.com/badges/sponsored-by-evil-martians.svg"
         alt="Sponsored by Evil Martians" width="236" height="54">
  </a>
</p>

[GitHub action]: https://github.com/andresz1/size-limit-action
[Statoscope]:    https://github.com/statoscope/statoscope
[cult-img]:      http://cultofmartians.com/assets/badges/badge.svg
[cult]:          http://cultofmartians.com/tasks/size-limit-config.html

## Who Uses Size Limit

* [MobX](https://github.com/mobxjs/mobx)
* [Material-UI](https://github.com/callemall/material-ui)
* [Autoprefixer](https://github.com/postcss/autoprefixer)
* [PostCSS](https://github.com/postcss/postcss) reduced
  [25% of the size](https://github.com/postcss/postcss/commit/150edaa42f6d7ede73d8c72be9909f0a0f87a70f).
* [Browserslist](https://github.com/browserslist/browserslist) reduced
  [25% of the size](https://github.com/browserslist/browserslist/commit/640b62fa83a20897cae75298a9f2715642531623).
* [EmojiMart](https://github.com/missive/emoji-mart) reduced
  [20% of the size](https://github.com/missive/emoji-mart/pull/111)
* [nanoid](https://github.com/ai/nanoid) reduced
  [33% of the size](https://github.com/ai/nanoid/commit/036612e7d6cc5760313a8850a2751a5e95184eab).
* [React Focus Lock](https://github.com/theKashey/react-focus-lock) reduced
  [32% of the size](https://github.com/theKashey/react-focus-lock/pull/48).
* [Logux](https://github.com/logux) reduced
  [90% of the size](https://github.com/logux/logux-client/commit/62b258e20e1818b23ae39b9c4cd49e2495781e91).

