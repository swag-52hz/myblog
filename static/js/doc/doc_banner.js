var img = document.getElementById('banner-img');
setInterval('change()', 5000);
var count = 1;
function change() {
			count++;
			if (count > 4) {
				count = 1;
			}
			judge(count);
		}
function  judge(a) {
    switch (a) {
        case 1:
            img.src = '../../../media/doc_banner_1.jpg';
            break;
        case 2:
            img.src = '../../../media/doc_banner_2.jpg';
            break;
        case 3:
            img.src = '../../../media/doc_banner_4.jpg';
            break;
    }
}