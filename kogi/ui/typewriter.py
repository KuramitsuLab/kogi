from .render import Doc

_CSS = """\
<style>
.var-highlight{
  color: #C0AD60;
}
.string-highlight{
  color: rgba(253, 149, 90, 0.8);
}
.typewriter{
    font-size: 2em;
    margin: 0;
    font-family: monotype;
    &:after{
      content: "|";
      animation: blink 500ms linear infinite alternate;
    }
}
@keyframes blink{
  0%{opacity: 0;}
  100%{opacity: 1;}
}
</style>
"""

_JS = """\
const typer = document.getElementById('typewriterZYX');
typewriter = setupTypewriter(typer);
typewriter.type();
"""

_HTML = """\
<pre id="typewriterZXY" class="typewriter">{}</pre>
"""


def typewriter_doc(text):
    return Doc.HTML(html=_HTML.format(text), text=text, css=_CSS, script=_JS)
