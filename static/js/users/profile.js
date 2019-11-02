let nav = document.getElementsByClassName('item');
let index = 0;
nav[index].id = "check";
for (let i = 0; i < nav.length; i++) {
    nav[i].onclick = function () {
        nav[index].id = "";
        index = i;
        nav[index].id = "check";
    }
}