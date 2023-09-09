class ImageExplorer extends HTMLElement {

      connectedCallback() {
        this.fetchUrl = this.getAttribute("data-images-url");
        this.root = this.attachShadow({ mode: "open" });
        const style = document.createElement("style");
        style.textContent = `ul {position: absolute; top:0, left:50%; min-width: 320px; z-index: 10000} li img {max-width: 240px;}`;
        this.root.appendChild(style);
      }

      show(callback) {
        this.callback = callback;
        this.ul = document.createElement("ul");

        fetch(this.fetchUrl).
        then((response) => response.json()).
        then((images) => {
            for (const image of images) {
              let li = document.createElement("li");
              let img = document.createElement("img");
              img.setAttribute("src", image.link);
              img.setAttribute("alt", image.name);
              img.setAttribute("data-link", image.link);
              img.addEventListener("click", (e) => this.selectImage({link: e.target.getAttribute("data-link"), name: e.target.alt}));
              li.appendChild(img);
              this.ul.appendChild(li);
            }
            let li = document.createElement("li");
            let input = document.createElement("input");
            input.setAttribute("type", "text"); input.setAttribute("name", "link");
            input.addEventListener("keyup", (e) => {if(e.key == "Enter") this.selectImage({link: e.target.value, name: "external image"})});
            let button = document.createElement("button");
            button.textContent = "Insert";
            button.addEventListener("click", (e) => this.selectImage({link: this.root.querySelector('input[name=link]').value, name: "external image"}));
            li.appendChild(input); li.appendChild(button);
            this.ul.appendChild(li);

            this.root.appendChild(this.ul);
        });
      }

      close() {
        this.ul.remove();
        this.callback = null;
        this.ul = null;
      }

      selectImage(imageData) {
        this.callback(imageData);
        this.close();
      }
}