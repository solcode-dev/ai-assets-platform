'use client';

import { Popover, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { Bell, Check, Trash2, Image as ImageIcon, Video,  Clock } from 'lucide-react';
import { useTaskStore, useUnreadCount} from '@/stores/useTaskStore';
import { formatDistanceToNow } from 'date-fns';
import { ko } from 'date-fns/locale';
import { motion, AnimatePresence } from 'framer-motion';

export function NotificationCenter() {
  const tasksObject = useTaskStore((state) => state.tasks);
  const { markAsRead, markAllAsRead, clearAllTasks, setSelectedJobId } = useTaskStore();
  const unreadCount = useUnreadCount();

  // 태스크를 최신순으로 정렬 (최신 30개만 표시)
  const sortedTasks = Object.values(tasksObject)
    .filter(task => ['COMPLETED', 'FAILED'].includes(task.status))
    .sort((a, b) => b.updatedAt - a.updatedAt)
    .slice(0, 30);

  return (
    <Popover className="relative">
      {({ open }) => (
        <>
          <Popover.Button
            className={`
              relative p-2 rounded-full transition-colors focus:outline-none
              ${open ? 'bg-gray-100 text-black' : 'text-gray-500 hover:bg-gray-50 hover:text-black'}
            `}
          >
            <Bell size={22} />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white border-2 border-white">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </Popover.Button>

          <Transition
            as={Fragment}
            enter="transition ease-out duration-200"
            enterFrom="opacity-0 translate-x-1"
            enterTo="opacity-100 translate-x-0"
            leave="transition ease-in duration-150"
            leaveFrom="opacity-100 translate-x-0"
            leaveTo="opacity-0 translate-x-1"
          >
            <Popover.Panel className="absolute left-14 top-0 mt-0 ml-2 w-80 sm:w-96 bg-white rounded-2xl shadow-xl border overflow-hidden z-50">
              <div className="flex items-center justify-between px-4 py-3 border-b bg-gray-50/50">
                <h3 className="font-semibold text-gray-900">알림</h3>
                <div className="flex gap-2">
                  {unreadCount > 0 && (
                    <button
                      onClick={() => markAllAsRead()}
                      className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1"
                    >
                      <Check size={14} /> 전부 읽음
                    </button>
                  )}
                  {sortedTasks.length > 0 && (
                    <button
                      onClick={() => {
                        if (confirm('모든 알림 이력을 삭제하시겠습니까?')) {
                          clearAllTasks();
                        }
                      }}
                      className="text-xs text-gray-500 hover:text-red-600 font-medium flex items-center gap-1"
                    >
                      <Trash2 size={14} /> 전체 삭제
                    </button>
                  )}
                </div>
              </div>

              <div className="max-h-[400px] overflow-y-auto">
                <AnimatePresence initial={false}>
                  {sortedTasks.length > 0 ? (
                    <div className="divide-y">
                      {sortedTasks.map((task) => (
                        <motion.div
                          key={task.id}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: 10 }}
                          className={`
                            group flex items-start gap-3 p-4 hover:bg-gray-50 transition-colors cursor-pointer
                            ${!task.isRead ? 'bg-blue-50/30' : ''}
                          `}
                          onClick={() => {
                            markAsRead(task.id);
                            if (task.status === 'COMPLETED') {
                              setSelectedJobId(task.id);
                            }
                          }}
                        >
                          <div className={`
                            p-2 rounded-xl shrink-0
                            ${task.status === 'COMPLETED' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'}
                          `}>
                            {task.mode === 'text-to-image' ? <ImageIcon size={18} /> : <Video size={18} />}
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex justify-between items-start mb-1">
                              <span className="text-xs font-semibold text-gray-400 uppercase tracking-tight">
                                {task.mode}
                              </span>
                              <span className="text-[10px] text-gray-400 flex items-center gap-1">
                                <Clock size={10} />
                                {formatDistanceToNow(task.updatedAt, { addSuffix: true, locale: ko })}
                              </span>
                            </div>
                            <p className={`text-sm leading-snug truncate ${!task.isRead ? 'font-semibold text-gray-900' : 'text-gray-600'}`}>
                              {task.status === 'COMPLETED' ? '작업이 성공적으로 완료되었습니다.' : '작업 생성에 실패했습니다.'}
                            </p>
                            <p className="text-xs text-gray-400 mt-1 line-clamp-1 italic">
                              ID: {task.id}
                            </p>
                          </div>

                          {!task.isRead && (
                            <div className="mt-2 h-2 w-2 rounded-full bg-blue-500 shrink-0" />
                          )}
                        </motion.div>
                      ))}
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
                      <div className="bg-gray-100 p-4 rounded-full mb-4">
                        <Bell size={32} className="text-gray-400 line-through opacity-50" />
                      </div>
                      <p className="text-gray-900 font-medium">최근 알림이 없습니다</p>
                      <p className="text-gray-500 text-sm mt-1">
                        새로운 이미지를 생성하면 완료 알림이 여기에 표시됩니다.
                      </p>
                    </div>
                  )
                  }
                </AnimatePresence>
              </div>
            </Popover.Panel>
          </Transition>
        </>
      )}
    </Popover>
  );
}
