
/*************************************************************************************************************************************************************************************
グローバル変数定義
    var group = 'CL法'; 'S法';
    var csrf_token = '{{ csrf_token }}';

*************************************************************************************************************************************************************************************/


/***酸化チタン　品質検討会資料***/
//銘柄を選択して、ランNO絞り込み
function __select__brand(value){
    $.ajax({
        url: "/isk_tools/reportoutput/" + group + "/品質検討会資料/__select__brand/",
        type: "POST",
        data : {
            'value': value,
            'csrfmiddlewaretoken': csrf_token
        },
        timeout: 10000,
        dataType: 'json',
        cache : false,
    })
    .done(function(data){
        $('#while').empty();
        $('#while').html(data.select);
    })
   .fail(function(jqXHR,textStatus,errorThrown){
        $('#while').empty();
        alert('Error!' +textStatus+' ' +errorThrown);
    });
}

//フォームチェックとパラメーター抽出、ダウンロード処理へ続く
function trace_report() {
    if($('#brand option:selected').length != 1){
        alert('銘柄を選択してください');
        return;
    }
    if($('#while option:selected').length > 3){
        alert('条件は3つまでです');
        return;
    }
    brand = document.getElementById('brand').value;
    selectedVals = $('#while').val();

    if(selectedVals.length == 1){
        run_no1 = selectedVals[0]
        run_no2 = selectedVals[0]
        run_no3 = selectedVals[0]
    }else if(selectedVals.length == 2){
        run_no1 = selectedVals[0]
        run_no2 = selectedVals[1]
        run_no3 = selectedVals[0]
    }else if(selectedVals.length == 3){
        run_no1 = selectedVals[0]
        run_no2 = selectedVals[1]
        run_no3 = selectedVals[2]
    }
    trace_report_download(brand, run_no1, run_no2, run_no3);
}

//データ生成してEXCELファイルダウンロード
function trace_report_download(brand, run_no1, run_no2, run_no3){
	var now = new Date();
	var timestamp = String(now.getFullYear()) + String(('0' + (now.getMonth() + 1)).slice(-2)) + String(('0' + now.getDate()).slice(-2)) +
	 String(now.getHours()) + String(now.getMinutes())
    var link_str = "/isk_tools/reportoutput/" + group + "/品質検討会資料/download/" + brand + "/" + run_no1 + "/" + run_no2 + "/" + run_no3 + "/";
    var downLoadLink = document.createElement("a");
    downLoadLink.download = timestamp + "_品質検討会資料(" + group + ").xlsx";
    downLoadLink.href = link_str;
    downLoadLink.click();
}

/***酸化チタン　トレースNO採番処理***/
//「酸化チタン_CL法_トレース採番MAIN処理」「酸化チタン_S法_トレースレポートMAIN処理」
function trace_no_numbering(){
    if($("#loading_gif") != null){
        $("#loading_gif").show();
    }
    $.ajax({
        url: "/isk_tools/reportoutput/品質検討会資料/トレースNO採番/",
        type: "POST",
        data : {
            'from_date': $('#from_date').val(),
            'to_date': $('#to_date').val(),
            'group': group,
            'csrfmiddlewaretoken': csrf_token
        },
        timeout: 1000000,
        dataType: 'json',
        cache : false,
    })
    .done(function(data){
        if($("#loading_gif") != null){
            $("#loading_gif").fadeOut();//呼び出し中に表示するgifをフェードアウト
        }
        alert(data.massage)
    })
   .fail(function(jqXHR,textStatus,errorThrown){
        if($("#loading_gif") != null){
            $("#loading_gif").fadeOut();//呼び出し中に表示するgifをフェードアウト
        }
        alert('Error!' +textStatus+' ' +errorThrown);
    });
}

/***機能材　トレースNO採番処理***/
function report_download(){
    console.log(document.getElementById('startTime').value);
    console.log(document.getElementById('endTime').value);
    var startTime = document.getElementById('startTime').value;
    var endTime = document.getElementById('endTime').value;
    var downLoadLink = document.createElement("a");
    downLoadLink.href = "./report/download/" + startTime + "/" + endTime + "/";
    downLoadLink.download = "品質日報.xlsx";
    downLoadLink.click();
}
