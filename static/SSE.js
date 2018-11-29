function sse() {
    var source = new EventSource('http://127.0.0.1:5001/stream');
    source.onmessage = function (event) {
        console.log(event.data);
        alert(event.data)
        document.getElementById('res').innerHTML += event.data + "<br/>";
    };
}
sse()