'use strict';


import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-app.js";
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-auth.js";


const firebaseConfig = {
    apiKey: "AIzaSyBwCIMq6xNocGnI3CsJCbNW2dVKFaByrWA",
    authDomain: "eloquent-optics-414512.firebaseapp.com",
    projectId: "eloquent-optics-414512",
    storageBucket: "eloquent-optics-414512.appspot.com",
    messagingSenderId: "595767030267",
    appId: "1:595767030267:web:93934332376b29f6371b5e"
};

window.addEventListener("load", function () {
    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);
    updateUI(document.cookie);
    console.log("hello world load");


    document.getElementById("sign-up").addEventListener('click', function () {
        const email = document.getElementById("email").value
        const password = document.getElementById("password").value

        createUserWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {
            
             const user = userCredential.user;

            
             user.getIdToken().then((token) => {
                document.cookie = "token=" + token + ";path=/;SameSite=Strict";
                window.location = "/";
             });

        })
        .catch((error) => {

                console.log(error.code + error.message);
        }) 
    });

    
    document.getElementById("login").addEventListener('click', function () {
        const email = document.getElementById("email").value
        const password = document.getElementById("password").value

        signInWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {
         
            const user = userCredential.user;
            console.log("logged in");


            user.getIdToken().then((token) => {
                document.cookie = "token=" + token + ";path=/;SameSite=Strict";
                window.location = "/";
            });


        })
        .catch((error) => {
           
            console.log(error.code + error.message);
        });
    });


    document.getElementById("sign-out").addEventListener('click', function () {
        signOut(auth)
        .then((output) => {
            
            document.cookie = "token=;path=/;SameSite=Strict";
            window.location = "/";
        });
    
    });
});

function updateUI(token) {
    var token = parseCookieToken(document.cookie);


    if(token.length > 0) {
        document.getElementById("login-box").hidden = true;
        document.getElementById("sign-out").hidden = false;
    } else {
        document.getElementById("login-box").hidden = false;
        document.getElementById("sign-out").hidden = true;
    }
};

function parseCookieToken(cookie) {
    
    var strings = cookie.split(";");



    for(let i = 0; i < strings.length; i++) {

        var temp = strings[i].split("=");
        if(temp[0].trim() === "token") 
            return temp[1];
    }


    return "";
    
};
    

