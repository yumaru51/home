
/*************************************************************************************************************************************************************************************
グローバル変数定義
    var ajax_next_step = '{% url 'ajax_next_step' %}';
    var ajax_department = '{% url 'ajax_department' %}';
    var ajax_user = '{% url 'ajax_user' %}';
    var csrf_token = '{{ csrf_token }}';

*************************************************************************************************************************************************************************************/


//次工程・次部署・次作業者変更時の処理
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

//部門変更時の処理
function department() {
        $.ajax({
            url: ajax_department,
            type: "POST",
            data: {
                'division': $('#id_division').val(),
                'csrfmiddlewaretoken': csrf_token
            },
            timeout: 10000,
            dataType: 'json',
            cache: false,
        })
        .done(function(data){
            $('#id_department').empty();
            $('#id_department').html(data.department);
            user();
        })
       .fail(function(jqXHR,textStatus,errorThrown){
            $('#id_department').empty();
            alert('Error!' +textStatus+' ' +errorThrown);
        });
}

//部署変更時の処理
function user() {
        $.ajax({
            url: ajax_user,
            type: "POST",
            data: {
                'department': $('#id_department').val(),
                'csrfmiddlewaretoken': csrf_token
            },
            timeout: 10000,
            dataType: 'json',
            cache: false,
        })
        .done(function(data){
            $('#id_user').empty();
            $('#id_user').html(data.user);
        })
       .fail(function(jqXHR,textStatus,errorThrown){
            $('#id_user').empty();
            alert('Error!' +textStatus+' ' +errorThrown);
        });
}
