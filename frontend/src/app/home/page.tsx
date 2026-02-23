"use client";

import React from "react";
import Link from "next/link";
import Image from "next/image";
import {
  ImageIcon,
  Video,
  Sparkles,
  ArrowRight,
  Zap,
  Layers,
  Shield,
  Terminal,
} from "lucide-react";
import { motion } from "framer-motion";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.12, duration: 0.5, ease: "easeOut" as const },
  }),
};

const features = [
  {
    icon: ImageIcon,
    title: "Text → Image",
    description:
      "텍스트 프롬프트 하나로 고해상도 이미지를 즉시 생성합니다. Imagen 3.0 모델 기반의 빠르고 정확한 결과물.",
    code: `POST /api/assets/generate
Content-Type: multipart/form-data

prompt: "A futuristic city at sunset"
mode: text-to-image`,
    gradient: "from-blue-500 to-cyan-400",
    bg: "bg-blue-500/10",
    border: "border-blue-500/20",
  },
  {
    icon: Video,
    title: "Text → Video",
    description:
      "프롬프트만으로 역동적인 비디오 클립을 만들어냅니다. Veo 3.0 기반의 차세대 비디오 생성 파이프라인.",
    code: `POST /api/assets/generate
Content-Type: multipart/form-data

prompt: "Drone flyover of mountains"
mode: text-to-video`,
    gradient: "from-purple-500 to-pink-400",
    bg: "bg-purple-500/10",
    border: "border-purple-500/20",
  },
  {
    icon: Sparkles,
    title: "Image → Video",
    description:
      "정적 이미지를 업로드하면 자연스러운 모션이 적용된 비디오로 변환합니다. 참조 이미지 기반 애니메이션.",
    code: `POST /api/assets/generate
Content-Type: multipart/form-data

prompt: "Gentle camera zoom in"
mode: image-to-video
source_image: [file]`,
    gradient: "from-amber-500 to-orange-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/20",
  },
];

const stats = [
  { icon: Zap, label: "평균 생성 시간", value: "< 10s", sub: "이미지 기준" },
  { icon: Layers, label: "지원 모드", value: "3가지", sub: "T2I · T2V · I2V" },
  {
    icon: Shield,
    label: "API 엔드포인트",
    value: "REST",
    sub: "SSE 실시간 알림",
  },
  {
    icon: Terminal,
    label: "스택",
    value: "Next.js",
    sub: "+ FastAPI + Celery",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 overflow-x-hidden">
      {/* ── Hero ── */}
      <section className="relative flex flex-col items-center justify-center text-center px-6 pt-32 pb-20">
        {/* glow background */}
        <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-blue-600/15 rounded-full blur-[120px] pointer-events-none" />

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="relative z-10"
        >
          <span className="inline-block mb-6 px-4 py-1.5 text-xs font-mono tracking-wider text-blue-400 border border-blue-500/30 rounded-full bg-blue-500/5">
            [JUNGLE] [AI Service Div.] Fullstack Product Engineer (인턴) 포지션 지원자 : 안소영

          </span>

          <h1 className="text-5xl md:text-7xl font-extrabold leading-tight tracking-tight">
            <span className="text-white">AI 멀티모달 </span>
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400">
              콘텐츠 생성 플랫폼 구축
            </span>
          </h1>

          <p className="mt-6 text-lg md:text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
            본 과제는 Google Vertex AI의 멀티모달 생성 AI 모델(Imagen, Veo)을
            활용해 게임 에셋을 생성하고 관리하는 통합 플랫폼을 구축하는
            작업입니다.
            <br className="hidden md:block" />
            사용자가 텍스트로 
이미지를 생성하고, 이미지나 텍스트로 비디오를 제작하는 서비스를 구축하는 것이 
목표입니다. 과제 수행 시 AI 도구를 자유롭게 사용하여 생산성을 높이세요.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/"
              className="group flex items-center gap-2 px-8 py-3.5 rounded-full font-semibold text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 shadow-lg shadow-blue-600/20 transition-all"
            >
              시작하기
              <ArrowRight
                size={18}
                className="group-hover:translate-x-1 transition-transform"
              />
            </Link>
            
          </div>
        </motion.div>
      </section>

      {/* ── Stats ── */}
      <section className="max-w-5xl mx-auto px-6 py-16">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {stats.map((s, i) => (
            <motion.div
              key={s.label}
              custom={i}
              variants={fadeUp}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              className="flex flex-col items-center gap-2 p-6 rounded-2xl bg-slate-900/60 border border-slate-800"
            >
              <s.icon size={20} className="text-blue-400" />
              <span className="text-2xl font-bold text-white">{s.value}</span>
              <span className="text-xs text-slate-500">{s.label}</span>
              <span className="text-[11px] text-slate-600 font-mono">
                {s.sub}
              </span>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Features ── */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <motion.h2
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-3xl md:text-4xl font-bold text-center mb-4"
        >
          세 가지 생성 모드
        </motion.h2>
        <p className="text-center text-slate-500 mb-16 max-w-xl mx-auto">
          각 모드는 독립된 AI 모델 파이프라인을 사용하며, 비동기 큐 기반으로 안정적으로 동작합니다.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              custom={i}
              variants={fadeUp}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              className={`group relative p-6 rounded-2xl bg-slate-900 border ${f.border} hover:border-opacity-60 transition-all hover:shadow-lg hover:shadow-black/20`}
            >
              {/* icon */}
              <div
                className={`w-12 h-12 ${f.bg} rounded-xl flex items-center justify-center mb-5`}
              >
                <f.icon
                  size={22}
                  className={`text-transparent bg-clip-text bg-gradient-to-br ${f.gradient}`}
                  style={{ stroke: "url(#grad)" }}
                />
                {/* fallback solid color */}
                <f.icon
                  size={22}
                  className="absolute text-blue-400 opacity-0"
                />
              </div>

              <h3 className="text-xl font-bold text-white mb-2">{f.title}</h3>
              <p className="text-sm text-slate-400 mb-5 leading-relaxed">
                {f.description}
              </p>

              {/* code block */}
              <div className="rounded-lg bg-slate-950 border border-slate-800 p-4 font-mono text-xs text-green-400/90 leading-relaxed whitespace-pre overflow-x-auto">
                {f.code}
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Architecture ── */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <motion.h2
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-3xl md:text-4xl font-bold text-center mb-4"
        >
          아키텍처
        </motion.h2>
        <p className="text-center text-slate-500 mb-12">
          비동기 작업 큐 기반의 확장 가능한 구조
        </p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="rounded-2xl bg-slate-900 border border-slate-800 p-4 overflow-hidden"
        >
          <Image
            src="/arch.jpeg"
            alt="시스템 아키텍처 다이어그램"
            width="100"
            height={600}
            className="w-full h-auto rounded-xl object-contain"
          />
        </motion.div>
      </section>

      {/* ── CTA ── */}
      <section className="text-center px-6 py-24">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
        >
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            지금 바로 시작하세요
          </h2>
          <p className="text-slate-500 mb-8">프롬프트 한 줄이면 충분합니다.</p>
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-10 py-4 rounded-full font-semibold text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 shadow-lg shadow-blue-600/20 transition-all text-lg"
          >
            Generate Now
            <ArrowRight size={20} />
          </Link>
        </motion.div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-slate-800 py-8 text-center text-xs text-slate-600 font-mono">
        Built with Next.js · FastAPI · Celery · Vertex AI
      </footer>
    </div>
  );
}
