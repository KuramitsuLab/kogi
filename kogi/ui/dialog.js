var timer = null;
var inputPane = document.getElementById('input');
inputPane.addEventListener('keydown', (e) => {
    if (e.keyCode == 13) {
        var text = inputPane.value;
        google.colab.kernel.invokeFunction('notebook.ask', [text], {});
        inputPane.value = '';
        if (timer !== null) {
            clearTimeout(timer);
        }
        // timer = setTimeout(() => {
        //     google.colab.kernel.invokeFunction('notebook.log', [], {});
        // }, 1000 * 60 * 5);
    }
});
inputPane.addEventListener('focusin', (e) => {
    inputPane.style.height = 200;
});
var like = (id, score) => {
    console.log(id, score)
    google.colab.kernel.invokeFunction('notebook.like', [id, score], {});
};
var copy = (id) => {
    const text = document.getElementById(`t${id}`).value;
    console.log(text);
    navigator.clipboard.writeText(text);
    //google.colab.kernel.invokeFunction('notebook.like', [id], {});
};
var say = (prompt, bid) => {
    const text = document.getElementById(`b${bid}`).textContent;
    google.colab.kernel.invokeFunction('notebook.say', [prompt, text], {});
};
// var target = document.getElementById('output');
// target.scrollIntoView(false);
