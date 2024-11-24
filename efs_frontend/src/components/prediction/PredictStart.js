import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ProgressBar, Container } from 'react-bootstrap';
import { ToastContainer, toast } from 'react-toastify'; // ใช้ toast เพื่อแจ้งเตือน
import 'react-toastify/dist/ReactToastify.css'; // CSS ของ toast
import BASE_URL from '../../api';

const PredictStart = () => {
  const [progress, setProgress] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const startPrediction = async () => {
      setLoading(true);
      setError(null);

      try {
        // ดึงข้อมูลปีและเดือนล่าสุดจาก API /current-month
        const responseLatest = await axios.get(`${BASE_URL}/current-month`);
        const { year, month } = responseLatest.data;  // เปลี่ยนเป็น 'year'

        // ตรวจสอบว่าค่า year ไม่ใช่ undefined
        if (!year) {
          throw new Error('No year data received from the API');
        }

        // ส่งคำขอพยากรณ์โดยใช้ปีและเดือนล่าสุด
        console.log("Sending data to API:", { year, month, modelName: "All" });
        const response = await axios.post(`${BASE_URL}/predict-or-fetch`, { 
          year: year,  // ใช้คีย์ 'year' ที่ถูกต้อง
          month: month,
          modelName: "All"
        });

        const { log } = response.data;

        // แสดงข้อความแจ้งเตือนความสำเร็จ
        toast.success(log); 

        // จำลอง progress bar
        let progressInterval = setInterval(() => {
          setProgress((oldProgress) => {
            if (oldProgress === 100) {
              clearInterval(progressInterval);
              setLoading(false);
              // Redirect ไปที่ /admin/predict
              navigate('/admin/predict');
            }
            return Math.min(oldProgress + 10, 100);
          });
        }, 500);

      } catch (error) {
        console.error('Prediction error:', error);
        setLoading(false);

        if (error.response) {
          console.log("Error response from API:", error.response.data);
          if (error.response.status === 404 && error.response.data.detail === "No predictions found for the specified year and month") {
            alert("ไม่พบข้อมูลพยากรณ์ กรุณาลองใหม่.");
          } else {
            alert("เกิดข้อผิดพลาดในการพยากรณ์ กรุณาลองใหม่.");
          }
        } else {
          // แสดงข้อผิดพลาดหากไม่สามารถรับค่า year จาก API ได้
          alert("เกิดข้อผิดพลาด: ไม่ได้รับค่าปีจาก API");
        }
      }
    };

    startPrediction();
  }, [navigate]);

  return (
    <Container style={{ marginTop: '50px' }}>
      <h3>กำลังเริ่มการพยากรณ์</h3>
      
      {/* แสดง progress bar */}
      <ProgressBar animated now={progress} label={`${progress}%`} />

      {/* ToastContainer สำหรับแจ้งเตือน */}
      <ToastContainer />
    </Container>
  );
};

export default PredictStart;
