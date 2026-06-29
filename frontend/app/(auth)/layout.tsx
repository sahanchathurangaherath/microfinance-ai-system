import type { ReactNode } from "react";
import { Shield, Lock, Brain, BarChart2, Building2 } from "lucide-react";

export default function AuthLayout({ children }: { children: ReactNode }) {


  return (
    <div className="flex min-h-screen w-screen overflow-hidden bg-slate-50">
      {/* Left Branding Panel */}
      <div className="hidden lg:flex flex-col justify-center w-[42%] min-h-screen bg-gradient-to-br from-slate-950 via-blue-900 to-indigo-700 relative overflow-hidden"> {/* FIX[BUG 7]: removed p-8 to use px-10 on inner wrapper */}
        {/* Grid pattern overlay */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff08_1px,transparent_1px),linear-gradient(to_bottom,#ffffff08_1px,transparent_1px)] bg-[size:24px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none" />
        
        {/* Soft glowing ambient blobs */}
        <div className="absolute top-[-10%] left-[-10%] w-[80%] h-[80%] rounded-full bg-blue-500/15 blur-[120px] pointer-events-none" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] rounded-full bg-indigo-500/15 blur-[100px] pointer-events-none" />

        {/* Centered content block */}
        <div className="relative z-10 flex flex-col gap-10 px-10 xl:px-16"> {/* FIX[BUG 7]: horizontal padding px-10 xl:px-16 */}
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center backdrop-blur-md border border-white/10">
              <Shield className="h-6 w-6 text-white" />
            </div>
            <span className="text-white text-xl font-bold tracking-tight">
              MicroFinance AI
            </span>
          </div>

          {/* Headlines & Feature rows */}
          <div>
            <h1 className="text-4xl font-extrabold text-white leading-tight mb-4 tracking-tight">
              Elevate Your
              <br />
              <span className="text-blue-300">Lending Impact</span>
            </h1>
            <p className="text-blue-100 text-base leading-relaxed max-w-sm mb-8">
              Streamline operations and make smarter lending decisions to better serve your communities.
            </p>


          </div>
        </div>

        {/* Bottom copyright notice */}
        <p className="absolute bottom-12 left-12 text-slate-400/80 text-xs tracking-wide">
          © {new Date().getFullYear()} MicroFinance AI System. All rights reserved.
        </p>
      </div>

      {/* Right Form Panel */}
      <div className="w-full lg:w-[58%] min-h-screen flex flex-col justify-center items-center p-4 sm:p-6 lg:p-8 bg-slate-50 relative overflow-y-auto overflow-x-hidden"> {/* FIX[BUG 7]: overflow-y-auto overflow-x-hidden instead of overflow-hidden */}
        {/* Subtle decorative grid/dot background for warmth and anchoring */}
        <div className="absolute inset-0 bg-[radial-gradient(#e2e8f0_1.5px,transparent_1.5px)] [background-size:32px_32px] opacity-70 pointer-events-none" />
        <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-blue-500/5 blur-[100px] pointer-events-none" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-indigo-500/5 blur-[100px] pointer-events-none" />

        <div className="w-full max-w-[440px] relative z-10">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <div className="w-8 h-8 rounded-lg bg-blue-700 flex items-center justify-center">
              <Shield className="h-5 w-5 text-white" />
            </div>
            <span className="text-[var(--text-primary)] text-lg font-bold">
              MicroFinance AI
            </span>
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}
