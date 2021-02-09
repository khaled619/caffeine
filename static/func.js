
jQuery(document).ready(function(){
	jQuery(".chosen").chosen({width: "100%"});
});

 // Chosen touch support.
 if ($('.chosen-container').length > 0) {
    $('.chosen-container').on('touchstart', function(e){
      e.stopPropagation(); e.preventDefault();
      // Trigger the mousedown event.
      $(this).trigger('mousedown');
    });
  }
// if inside main page load the animation
if(window.location.pathname === '/')
{
    document.addEventListener("DOMContentLoaded", function(event) { 
        var slideIndex = 0;
        showSlides();
        function showSlides()
        {
            var i;
            var slides = document.getElementsByClassName("mySlides");
            var dots = document.getElementsByClassName("dot");
            for(i = 0; i < slides.length; i++)
            {
                slides[i].style.display = "none";
            }
            slideIndex++;
            if (slideIndex > slides.length)
            {
                slideIndex = 1
            }
            for(i = 0; i < dots.length; i++)
            {
                dots[i].className = dots[i].className.replace(" active", "");
            }
            slides[slideIndex-1].style.display = "block";
            dots[slideIndex-1].className += " active";
            setTimeout(showSlides, 4000);
        }
    });
}

if(window.location.pathname === '/profile')
{
    document.addEventListener('DOMContentLoaded', function()
    {
        
        const weight = document.querySelector("#weight")
        weight.onkeyup = function()
        {
            weightToCheck = weight.value
            if (!isNaN(weightToCheck))
            {
                if(weightToCheck < 0)
                {
                    // if not a positive number error
                    document.getElementById("weight").style.border = "2px solid #ff0000";
                    document.getElementById("weightError").innerHTML = `Weight must be a positive integer`
                }
                else
                {
                    document.getElementById("weight").style.border = "2px solid #69ff69";
                    document.getElementById("weightError").innerHTML = ``
                }
            }
            else
            {
                document.getElementById("weight").style.border = "2px solid #ff0000";
                document.getElementById("weightError").innerHTML = `Weight must be a positive integer`
            }
        }
    });
}


url = window.location.href;
if(url.match("reset_password"))
{
    document.addEventListener('DOMContentLoaded', function()
    {
        const submit = document.querySelector('#submit');
        const checkPassword = document.querySelector('#password');
        const checkConfirmation = document.querySelector('#confirmation');
        checkPassword.onkeyup = function()
        {
            if(checkPassword.value.length < 8)
            {
                document.getElementById("password").style.border = "2px solid #ff0000";
                document.getElementById("passError").innerHTML = `Password must be at least 8 characters`;
            }
            else
            {
                document.getElementById("password").style.border = "2px solid #69ff69";
                document.getElementById("passError").innerHTML = ``;
            }
        };
        checkConfirmation.onkeyup = function()
        {
            if(checkConfirmation.value != checkPassword.value)
            {
                document.getElementById("confirmation").style.border = "2px solid #ff0000";
                document.getElementById("confrimationError").innerHTML = `Passwords must match`;
            }
            else
            {
                document.getElementById("confirmation").style.border = "2px solid #69ff69";
                document.getElementById("confrimationError").innerHTML = ``;
            }
        };
    });
}
//only execute on register page
if(window.location.pathname === '/register')
{
    document.addEventListener('DOMContentLoaded', function()
    {
        const checkUsername = document.querySelector('#username');
        const submit = document.querySelector('#submit');
        const checkPassword = document.querySelector('#password');
        const checkConfirmation = document.querySelector('#confirmation');
        const checkEmail = document.querySelector('#email');
        checkPassword.onkeyup = function()
        {
            if(checkPassword.value.length < 8)
            {
                document.getElementById("password").style.border = "2px solid #ff0000";
                document.getElementById("passError").innerHTML = `Password must be at least 8 characters`;
            }
            else
            {
                document.getElementById("password").style.border = "2px solid #69ff69";
                document.getElementById("passError").innerHTML = ``;
            }
        };
        checkConfirmation.onkeyup = function()
        {
            if(checkConfirmation.value != checkPassword.value)
            {
                document.getElementById("confirmation").style.border = "2px solid #ff0000";
                document.getElementById("confrimationError").innerHTML = `Passwords must match`;
            }
            else
            {
                document.getElementById("confirmation").style.border = "2px solid #69ff69";
                document.getElementById("confrimationError").innerHTML = ``;
            }
        };

        checkUsername.onkeyup = function()
        {
            if(checkUsername.value.length < 3)
            {
                document.getElementById("username").style.border = "2px solid #ff0000";
                document.getElementById("usernameError").innerHTML = `username must be at least 3 characters`;
            }
            else
            {
                document.getElementById("username").style.border = "2px solid #69ff69";
                document.getElementById("usernameError").innerHTML = ``;
            }
        };
    });
}


