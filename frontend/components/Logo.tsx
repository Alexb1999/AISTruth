import Link from "next/link";

type LogoSize = "sm" | "nav" | "md" | "lg";

type LogoProps = {
  size?: LogoSize;
  href?: string;
  className?: string;
  priority?: boolean;
};

const LOGO = { src: "/aistruth-logo@2x.png", srcSet: "/aistruth-logo.png 1x, /aistruth-logo@2x.png 2x" } as const;

type SizeConfig = { img: string; clip?: string };

/** Nav clips the tagline so the compass + wordmark fill the visible height. */
const SIZE: Record<LogoSize, SizeConfig> = {
  sm: { img: "h-10 w-auto max-w-none" },
  nav: {
    clip: "block h-[4.625rem] overflow-hidden sm:h-[5.875rem]",
    img: "relative -top-1.5 h-[6.75rem] w-auto max-w-none sm:-top-2 sm:h-[8.5rem]",
  },
  md: { img: "h-16 w-auto max-w-none sm:h-[4.25rem]" },
  lg: { img: "h-20 w-auto max-w-none sm:h-24" },
};

export default function Logo({ size = "md", href = "/", className = "", priority = false }: LogoProps) {
  const cfg = SIZE[size] ?? SIZE.sm;

  const image = (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={LOGO.src}
      srcSet={LOGO.srcSet}
      alt="AISTruth — Maritime AIS Integrity"
      className={`block ${cfg.img}`}
      decoding="async"
      fetchPriority={priority ? "high" : "auto"}
    />
  );

  const content = cfg.clip ? <span className={cfg.clip}>{image}</span> : image;

  if (href) {
    return (
      <Link
        href={href}
        className={`inline-flex shrink-0 items-center leading-none ${size === "nav" ? "-translate-y-1.5 sm:-translate-y-2" : ""} ${className} transition hover:opacity-90`}
        aria-label="AISTruth home"
      >
        {content}
      </Link>
    );
  }

  return <div className={`inline-flex shrink-0 items-center leading-none ${className}`}>{content}</div>;
}
