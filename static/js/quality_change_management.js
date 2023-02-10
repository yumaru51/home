
/*************************************************************************************************************************************************************************************
グローバル変数定義
    var ajax_next_step = '{% url 'ajax_next_step' %}';
    var ajax_department = '{% url 'ajax_department' %}';
    var ajax_user = '{% url 'ajax_user' %}';
    var ajax_file_upload = '{% url 'quality_change_management:ajax_file_upload' %}';
    var ajax_file_list = '{% url 'quality_change_management:ajax_file_list' %}';
    var ajax_file_delete = '{% url 'quality_change_management:ajax_file_delete' %}';
    var csrf_token = '{% csrf_token %}';

*************************************************************************************************************************************************************************************/


//次工程・次部署・次作業者変更時の絞り込み処理
function next_step() {
    $.ajax({
        url: ajax_next_step,
        type: "POST",
        data: {
            'next_step': $('#next_step').val(),
            'next_department': $('#next_department').val(),
            'next_operator': $('#next_operator').val(),
            'csrfmiddlewaretoken': csrf_token
        },
        timeout: 10000,
        dataType: 'json',
        cache: false,
    })
    .done(function(data){
        $('#next_step').empty();
        $('#next_step').html(data.next_step);
        $('#next_department').empty();
        $('#next_department').html(data.next_department);
        $('#next_operator').empty();
        $('#next_operator').html(data.next_operator);
    })
    .fail(function(jqXHR,textStatus,errorThrown){
        $('#next_step').empty();
        alert('Error!' +textStatus+' ' +errorThrown);
        $('#next_department').empty();
        alert('Error!' +textStatus+' ' +errorThrown);
        $('#next_operator').empty();
        alert('Error!' +textStatus+' ' +errorThrown);
    });
}


//部門変更時の部署リスト絞り込み処理
function department(id_division, id_department, id_user) {
    $.ajax({
        url: ajax_department,
        type: "POST",
        data: {
            'division': $('#' + id_division).val(),
            'csrfmiddlewaretoken': csrf_token
        },
        timeout: 10000,
        dataType: 'json',
        cache: false,
    })
    .done(function(data){
        $('#' + id_department).empty();
        $('#' + id_department).html(data.department);
        user(id_department, id_user);
    })
    .fail(function(jqXHR,textStatus,errorThrown){
        $('#' + id_department).empty();
        alert('Error!' +textStatus+' ' +errorThrown);
    });
}


//部署変更時のユーザーリスト絞り込み処理
function user(id_department, id_user){
    $.ajax({
        url: ajax_user,
        type: "POST",
        data: {
            'department': $('#' + id_department).val(),
            'csrfmiddlewaretoken': csrf_token
        },
        timeout: 10000,
        dataType: 'json',
        cache: false,
    })
    .done(function(data){
        $('#' + id_user).empty();
        $('#' + id_user).html(data.user);
    })
    .fail(function(jqXHR,textStatus,errorThrown){
        $('#' + id_user).empty();
        alert('Error!' +textStatus+' ' +errorThrown);
    });
}


//添付ファイルアップロード処理
function file_upload(form_id){
    form_id = '#' + form_id
    var form_data = new FormData($(form_id).get(0));

    //file_budget_idが無効、もしくはtargetに指定された側のidが無効の場合はアップロード停止
    if( (form_data.get('file_budget_id') == 0) || (form_data.get('file_target') == 'work' && form_data.get('file_work_id') == 0) ){
        alert('ID未指定のためファイルをアップロードできません、先に保存してください');
        // アクションボタン有効化
        $(".button").prop("disabled", false);
        cancelFlag = false;
        return;
    }

    // POSTでアップロード
    $.ajax({
        url         : ajax_file_upload,
        type        : "POST",
        data        : form_data,
        cache       : false,
        contentType : false,
        processData : false,
        dataType    : "json"
    })
    .done(function(data){
        alert(data.msg);
        console.log('file_upload')
        file_list();
    })
    .fail(function(jqXHR,textStatus,errorThrown){
        alert('Error!' +textStatus+' ' +errorThrown);
    });
    setTimeout(function () {
        // アクションボタン有効化
        $(".button").prop("disabled", false);
        cancelFlag = false;
    }, 2000);
}


//添付ファイルリスト表示処理
function file_list() {
    $.ajax({
        url         : ajax_file_list,
        type        : "POST",
        data        : {
            'csrfmiddlewaretoken': csrf_token
        },
        timeout     : 10000,
        dataType    : "json",
        cache       : false,
    })
    .done(function(data){
        $('#file_list').empty();
        $('#file_list').html(data.html);
    })
    .fail(function(jqXHR,textStatus,errorThrown){
        $('#file_list').empty();
        alert('Error!' +textStatus+' ' +errorThrown);
    });
}


//添付ファイルダウンロード処理
function file_download(data_id, file_name){
    var link_str = ajax_file_list + data_id + "/" + file_name + "/";
    var downLoadLink = document.createElement("a");
    downLoadLink.download = file_name;
    downLoadLink.href = link_str ;
    downLoadLink.click();
}


//添付ファイル削除処理
function file_delete(file_name){
    $.ajax({
        url         : ajax_file_delete,
        type        : "POST",
        data        : {
            'file_name' : file_name,
            'csrfmiddlewaretoken': csrf_token
        },
        timeout     : 10000,
        dataType    : 'json',
        cache       : false,
    })
    .done(function(data){
        alert(data.msg);
        console.log('file_delete')
        file_list();
    })
   .fail(function(jqXHR,textStatus,errorThrown){
        alert('Error!' +textStatus+' ' +errorThrown);
    });
}


//レベル判定表ダウンロード処理
function level_judgment_table_download(){
    var link_str = "\\\\ydomnserv\\common\\部門間フォルダ\\FacilityData\\template_files\\quality_change_management\\変更管理レベル分表.xlsx";
    var downLoadLink = document.createElement("a");
    downLoadLink.download = '変更管理レベル分表.xlsx';
    downLoadLink.href = link_str ;
    downLoadLink.click();
}


//チェックボックス最低1つ以上選択させる
$(function(){
//    $("input[type='checkbox']").on('change', function () {
//    $('.form-check-inline_change_target').on('change', function () {
    $('.form-check-inline_change_target').on("click",function(){
        status_check();
    });
});


//「change_target」の状態チェック
function status_check(){
    if( $('.form-check-inline_change_target:checked').length > 0 ){
       $('.form-check-inline_change_target').prop("required",false); //required属性の解除
    }else{
       $('.form-check-inline_change_target').prop("required",true); //required属性の付与
    }
}

