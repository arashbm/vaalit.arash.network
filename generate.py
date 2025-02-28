import argparse
import sys
import json
from pathlib import Path
import shutil
import time

from markdown2 import Markdown
import jinja2

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


def compile_site(output_dir):
    template = jinja2.Template(open("template.j2").read())
    markdowner = Markdown()

    for language in ["en", "sv", "fi"]:
        print(f"Generating {language}", file=sys.stderr)

        with open(f"{language}/dict.json") as df:
            dictionary = json.load(df)

        for p in Path(language).glob("*.md"):
            dictionary[p.stem] = markdowner.convert(p.read_text())

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        filename = language
        if language == "fi":
            filename = "index"

        with open(f"{output_dir}/{filename}.html", "w") as f:
            f.write(template.render(dictionary))

    shutil.copytree("static", f"{output_dir}/", dirs_exist_ok=True)


class RecompileHandler(FileSystemEventHandler):
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.observer = Observer()
        self.observer.schedule(self, path="template.j2", recursive=False)
        self.observer.schedule(self, path="generate.py", recursive=False)
        self.observer.schedule(self, path="static", recursive=True)
        for language in ["en", "sv", "fi"]:
            self.observer.schedule(self, path=language, recursive=True)

    def start(self):
        self.observer.start()
        try:
            while True:
                time.sleep(2)
        except KeyboardInterrupt:
            self.observer.stop()

        self.observer.join()

    def on_modified(self, event):
        self.comp(event)

    def on_created(self, event):
        self.comp(event)

    # def on_deleted(self, event):
    #     self.comp(event)

    def comp(self, event):
        if event.src_path.endswith("~"):
            return
        print(f"Detected change in {event.src_path}", file=sys.stderr)
        print(f"event: {event}", file=sys.stderr)
        try:
            compile_site(self.output_dir)
        except Exception as e:
            print(f"Error during compilation: {e}", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="out",
                        help="output directory")
    parser.add_argument("--watch", action="store_true",
                        help="Watch files and recompile on changes")
    args = parser.parse_args()

    compile_site(args.output_dir)

    if args.watch:
        event_handler = RecompileHandler(args.output_dir)
        event_handler.start()
