import React, { useState, useEffect, useRef } from "react";
import { ReactMic } from "react-mic";
import "./Alarmdesign.css";

const AlarmApp = () => {
  const [alarmTime, setAlarmTime] = useState("");
  const [isAlarmActive, setIsAlarmActive] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [amPm, setAmPm] = useState("AM");
  const [exerciseType, setExerciseType] = useState("Pushups");
  const [exerciseCount, setExerciseCount] = useState("3");
  const [tasks, setTasks] = useState([]);
  const [taskInput, setTaskInput] = useState("");
  const [isFeedLoading, setIsFeedLoading] = useState(false);
  const alarmSoundRef = useRef(new Audio());

  // Alarm time check
  useEffect(() => {
    const checkAlarm = setInterval(() => {
      if (!alarmTime) return;
      const currentTime = new Date();
      const [hours, minutes] = alarmTime.split(":").map(Number);
      const alarmHours = amPm === "AM" ? hours : (hours % 12) + 12;

      if (
        currentTime.getHours() === alarmHours &&
        currentTime.getMinutes() === minutes &&
        currentTime.getSeconds() === 0
      ) {
        setIsAlarmActive(true);
        playAlarm();
        triggerExerciseDetection();
      }
    }, 1000);

    return () => clearInterval(checkAlarm);
  }, [alarmTime, amPm]);

  // Polling to check if pushup goal is met
  useEffect(() => {
    let pollInterval;
    if (isAlarmActive) {
      pollInterval = setInterval(async () => {
        try {
          const response = await fetch("http://localhost:5000/check-pushup-status");
          const data = await response.json();
          if (data.completed) {
            stopAlarm();
          }
        } catch (error) {
          console.error("Error polling pushup status:", error);
        }
      }, 1000);
    }
    return () => clearInterval(pollInterval);
  }, [isAlarmActive]);

  const playAlarm = () => {
    if (recordedBlob) {
      alarmSoundRef.current.src = URL.createObjectURL(recordedBlob.blob);
      alarmSoundRef.current.loop = true;
      alarmSoundRef.current.play().then(() => {
        if (document.documentElement.requestFullscreen) {
          document.documentElement.requestFullscreen();
        }
      });
    }
  };

  const stopAlarm = () => {
    setIsAlarmActive(false);
    alarmSoundRef.current.pause();
    alarmSoundRef.current.currentTime = 0;
    if (document.fullscreenElement) {
      document.exitFullscreen();
    }
  };

  const triggerExerciseDetection = async () => {
    try {
      setIsFeedLoading(true);
      const response = await fetch("http://localhost:5000/start-detection", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          exercise: exerciseType,
          count: parseInt(exerciseCount),
        }),
      });
      const data = await response.json();
      console.log("Exercise detection started:", data);
      setTimeout(() => setIsFeedLoading(false), 1000);
    } catch (error) {
      console.error("Failed to start exercise detection:", error);
      setIsFeedLoading(false);
    }
  };

  const handleRecording = (state) => setIsRecording(state);
  const onStopRecording = (recordedBlob) => setRecordedBlob(recordedBlob);

  const handleSetAlarm = () => {
    if (alarmTime) {
      alert(`Alarm set for ${alarmTime} ${amPm} with ${exerciseCount} ${exerciseType}`);
    } else {
      alert("Please set a valid time for the alarm.");
    }
  };

  const addTask = () => {
    if (taskInput && tasks.length < 4) {
      setTasks([...tasks, taskInput]);
      setTaskInput("");
    }
  };

  const removeTask = (index) => setTasks(tasks.filter((_, i) => i !== index));

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Smart Alarm</h1>
      </header>

      <main className="app-main">
        <section className="alarm-section card">
          <h2>Set Alarm</h2>
          <div className="alarm-controls">
            <input
              type="time"
              value={alarmTime}
              onChange={(e) => setAlarmTime(e.target.value)}
              className="time-input"
            />
            <select
              value={amPm}
              onChange={(e) => setAmPm(e.target.value)}
              className="ampm-select"
            >
              <option value="AM">AM</option>
              <option value="PM">PM</option>
            </select>
            <button onClick={handleSetAlarm} className="btn btn-primary">
              Set Alarm
            </button>
          </div>
        </section>

        {isAlarmActive && (
          <section className="alarm-active card">
            <div className="webcam-container">
              {isFeedLoading ? (
                <p>Loading video feed...</p>
              ) : (
                <img
                  src="http://localhost:5000/video-feed"
                  alt="Pushup Detection Feed"
                  className="webcam"
                  onError={(e) => console.error("Failed to load video feed:", e)}
                />
              )}
            </div>
          </section>
        )}

        <section className="exercise-section card">
          <h2>Choose Wakeup Action</h2>
          <div className="exercise-controls">
            <label>Exercise:</label>
            <select
              value={exerciseType}
              onChange={(e) => setExerciseType(e.target.value)}
              className="exercise-select"
            >
              <option value="Pushups">Pushups</option>
              <option value="squats">Squats</option>
            </select>
            <label>Repetitions:</label>
            <select
              value={exerciseCount}
              onChange={(e) => setExerciseCount(e.target.value)}
              className="exercise-select"
            >
              {["3", "4", "5", "6", "7", "8"].map((count) => (
                <option key={count} value={count}>
                  {count}
                </option>
              ))}
            </select>
          </div>
        </section>

        <section className="recorder-section card">
          <h2>Record WAKE-UP Tone</h2>
          <div className="recorder-controls">
            <button
              onClick={() => handleRecording(true)}
              className="btn btn-secondary"
            >
              Start Recording
            </button>
            <button
              onClick={() => handleRecording(false)}
              className="btn btn-secondary"
            >
              Stop Recording
            </button>
            <ReactMic
              record={isRecording}
              onStop={onStopRecording}
              strokeColor="#000000"
              backgroundColor="#FF4081"
              className="sound-wave"
            />
          </div>
        </section>

        <section className="todo-section card">
          <h2>Task-To-Be-Done(After wakeup)</h2>
          <ul className="task-list">
            {tasks.map((task, index) => (
              <li key={index} className="task-item">
                {task}
                <button
                  onClick={() => removeTask(index)}
                  className="btn btn-danger"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
          {tasks.length < 4 && (
            <div className="task-input">
              <input
                type="text"
                value={taskInput}
                onChange={(e) => setTaskInput(e.target.value)}
                placeholder="Add a task"
                className="task-text"
              />
              <button onClick={addTask} className="btn btn-primary">
                Add Task
              </button>
            </div>
          )}
        </section>
      </main>
    </div>
  );
};

export default AlarmApp;