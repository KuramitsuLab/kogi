var timer = null;
var inputPane = document.getElementById('input');
inputPane.addEventListener('keydown', (e) => {
    if (e.keyCode == 13) {
        var text = inputPane.value;
        google.colab.kernel.invokeFunction('notebook.ask', [text], {});
        inputPane.value = '';
        // if (timer !== null) {
        //     clearTimeout(timer);
        // }
        // timer = setTimeout(() => {
        //     google.colab.kernel.invokeFunction('notebook.log', [], {});
        // }, 1000 * 60 * 5);
    }
});
inputPane.addEventListener('focusin', (e) => {
    inputPane.style.height = 200;
});
var like = (id, score) => {
    google.colab.kernel.invokeFunction('notebook.like', [id, score], {});
};
var copy = (id) => {
    const text = document.getElementById(`t${id}`).value;
    navigator.clipboard.writeText(text);
    //google.colab.kernel.invokeFunction('notebook.like', [id], {});
};
var say = (prompt, bid) => {
    const text = document.getElementById(`b${bid}`).textContent;
    google.colab.kernel.invokeFunction('notebook.say', [prompt, text], {});
};
const setupTypewriter = (t) => {
    var HTML = t.innerHTML;
    t.innerHTML = "";
    var cursorPosition = 0,
        tag = "",
        writingTag = false,
        tagOpen = false,
        typeSpeed = 100,
        tempTypeSpeed = 0;
    var type = () => {
        if (writingTag === true) {
            tag += HTML[cursorPosition];
        }
        if (HTML[cursorPosition] === "<") {
            tempTypeSpeed = 0;
            if (tagOpen) {
                tagOpen = false;
                writingTag = true;
            } else {
                tag = "";
                tagOpen = true;
                writingTag = true;
                tag += HTML[cursorPosition];
            }
        }
        if (!writingTag && tagOpen) {
            tag.innerHTML += HTML[cursorPosition];
        }
        if (!writingTag && !tagOpen) {
            if (HTML[cursorPosition] === " ") {
                tempTypeSpeed = 0;
            }
            else {
                tempTypeSpeed = (Math.random() * typeSpeed) + 50;
            }
            t.innerHTML += HTML[cursorPosition];
        }
        if (writingTag === true && HTML[cursorPosition] === ">") {
            tempTypeSpeed = (Math.random() * typeSpeed) + 50;
            writingTag = false;
            if (tagOpen) {
                var newSpan = document.createElement("span");
                t.appendChild(newSpan);
                newSpan.innerHTML = tag;
                tag = newSpan.firstChild;
            }
        }
        cursorPosition += 1;
        if (cursorPosition < HTML.length - 1) {
            setTimeout(type, tempTypeSpeed);
        }
    };
    return {
        type: type
    };
}

// var target = document.getElementById('output');
// target.scrollIntoView(false);
