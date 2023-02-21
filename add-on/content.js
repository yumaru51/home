window.alert('アプリ開いたね！');



(function() {

var newElement = document.createElement("p"); // p要素作成
var newContent = document.createTextNode("子要素３"); // テキストノードを作成
newElement.appendChild(newContent); // p要素にテキストノードを追加
newElement.setAttribute("id","child-p3"); // p要素にidを設定
var newElement = document.createElement("p"); // p要素作成
var newContent = document.createTextNode("子要素３"); // テキストノードを作成
newElement.appendChild(newContent); // p要素にテキストノードを追加
newElement.setAttribute("id","child-p3"); // p要素にidを設定
var parentDiv = document.getElementById("parent-div");
parentDiv.appendChild(newElement);

}());