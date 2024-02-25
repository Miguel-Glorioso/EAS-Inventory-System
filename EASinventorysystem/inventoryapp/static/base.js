const body = document.querySelector("body"),
  sidebar = body.querySelector(".sidebar"),
  toggle = body.querySelector(".toggle");

  toggle.addEventListener("click", () =>{
    sidebar.classList.toggle("close");
  });

  navLinks.forEach(navLink => {
    navLink.addEventListener("mouseenter", () => {
      if (sidebar.classList.contains("close")) {
        navLink.querySelector(".tooltip").style.opacity = "1";
      }
    });
  
    navLink.addEventListener("mouseleave", () => {
      if (sidebar.classList.contains("close")) {
        navLink.querySelector(".tooltip").style.opacity = "0";
      }
    });
  });