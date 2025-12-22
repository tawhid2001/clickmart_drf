export default function Footer() {
  return (
    <footer className="w-full py-4 border-t flex flex-col items-center text-sm text-gray-600 text-center">
      <p className="flex flex-col items-center gap-1">
        Developed with <span className="text-red-500">❤️</span> by{" "}
        <a
          href="https://www.linkedin.com/in/tawhid-talal/"
          target="_blank"
          className="text-blue-600 hover:underline"
        >
          Tawhid Talal
        </a>
      </p>

      <div className="flex flex-col items-center gap-1 mt-2">
        <a
          href="mailto:tawhid.talal@gmail.com"
          className="text-blue-600 hover:underline"
        >
          tawhid.talal@gmail.com{" "}
        </a>

        <span className="flex items-center gap-1 text-gray-500 text-sm">
          <i className="bi bi-geo-alt-fill" style={{ fontSize: "20px" }}></i>
          Maryland, USA
        </span>
      </div>
    </footer>
  );
}

