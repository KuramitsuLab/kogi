var inputPane = document.getElementById("inputXYZ");
inputPane.addEventListener('keydown', (e) => {
    if (e.keyCode == 13) {
        var text = inputPane.value;
        google.colab.kernel.invokeFunction('notebook.ask', [text], {});
        inputPane.value = '';
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
