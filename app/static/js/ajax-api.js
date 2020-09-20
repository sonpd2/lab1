

function functionName(){
// Attach a submit handler to the form
$( ".iptables" ).submit(function( event ) {

    // Stop form from submitting normally
    event.preventDefault();
    var $serverid = ($(this).attr("value"));
    var $token =  $('input[name="csrf_token"]').attr('value');
    var $button =  $('button[name="'+ $serverid + '"]');
    var $loading =  $('img[name="' + $serverid +  '"]');


    $button.hide()
    $loading.show()
    // Send the data using post
    var posting = $.post( '/api/iptables/' + $serverid,{ "csrf_token": $token });
    // Put the results in a div
    posting.done(function( data ) {

    const Toast = Swal.mixin({
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 5000,
            timerProgressBar: true,
            onOpen: (toast) => {
            toast.addEventListener('mouseenter', Swal.stopTimer)
            toast.addEventListener('mouseleave', Swal.resumeTimer)
        }
    })

    Toast.fire({
        icon: 'success',
        title: 'Result for check ' + $serverid + ' : ' +  data.data
    })

    $loading.hide();
    $button.empty().append( data.data ).show();
});

});
}