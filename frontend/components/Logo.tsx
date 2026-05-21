import Link from "next/link";

type LogoSize = "sm" | "nav" | "md" | "lg";

type LogoProps = {
  size?: LogoSize;
  href?: string;
  className?: string;
  priority?: boolean;
};

const LOGO_FULL = {
  src: "/aistruth-logo@2x.png",
  srcSet: "/aistruth-logo.png 1x, /aistruth-logo@2x.png 2x",
} as const;

const LOGO_NAV = {
  src: "/aistruth-logo-nav@2x.png",
  srcSet: "/aistruth-logo-nav.png 1x, /aistruth-logo-nav@2x.png 2x",
} as const;

type LogoAsset = { src: string; srcSet: string };

type SizeConfig = { asset: LogoAsset; img: string };

const SIZE: Record<LogoSize, SizeConfig> = {
  sm: { asset: LOGO_NAV, img: "h-8 w-auto max-w-[9rem]" },
  nav: { asset: LOGO_NAV, img: "h-8 w-auto max-w-[10rem] sm:h-9" },
  md: { asset: LOGO_FULL, img: "h-10 w-auto max-w-[11rem] sm:h-11" },
  lg: { asset: LOGO_FULL, img: "h-12 w-auto max-w-[13rem] sm:h-14" },
};

export default function Logo({ size = "md", href = "/", className = "", priority = false }: LogoProps) {
  const cfg = SIZE[size] ?? SIZE.md;

  const image = (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={cfg.asset.src}
      srcSet={cfg.asset.srcSet}
      alt="AISTruth"
      className={`block ${cfg.img}`}
      decoding="async"
      fetchPriority={priority ? "high" : "auto"}
    />
  );

  if (href) {
    return (
      <Link
        href={href}
        className={`inline-flex shrink-0 items-center leading-none ${className} transition hover:opacity-90`}
        aria-label="AISTruth home"
      >
        {image}
      </Link>
    );
  }

  return <div className={`inline-flex shrink-0 items-center leading-none ${className}`}>{image}</div>;
}
